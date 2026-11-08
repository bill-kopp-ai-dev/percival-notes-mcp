"""Static contract checks for the Notes MCP image.

Two owners, one init. The launcher owns the init layer (``docker run
--init`` / Compose ``init: true``) and the image embeds none: a tini in
the image would stack a second supervision layer on top of the
launcher's own init and mask which process is actually responsible for
SIGTERM.

These tests read the deployment files as text, so they need no Docker
daemon and catch the drift before it reaches CI.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "docker-compose.yml"
README = REPO_ROOT / "README.md"


def _instructions(path: Path) -> str:
    """Return the file's instructions, without the comment lines."""
    text = path.read_text(encoding="utf-8")
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _runtime_instructions() -> str:
    """Return the Dockerfile instructions with shell continuations joined."""
    return re.sub(r"\\\s*\n\s*", " ", _instructions(DOCKERFILE))


def _removed_paths() -> set[str]:
    """Return every path the runtime stage deletes."""
    removed: set[str] = set()
    for command in re.split(r"&&|\n", _runtime_instructions()):
        command = command.strip()
        if not command.startswith("rm "):
            continue
        for argument in command.split()[1:]:
            if argument.startswith("-"):
                continue
            removed.add(argument.rstrip("/"))
    return removed


def _service_block(contents: str, service_name: str) -> str:
    """Return one top-level Compose service block for focused checks."""
    start = re.search(rf"^  {re.escape(service_name)}:\s*$", contents, re.MULTILINE)
    assert start, f"Compose service {service_name!r} must exist"
    next_service = re.search(r"^  [a-zA-Z0-9_-]+:\s*$", contents[start.end() :], re.MULTILINE)
    end = start.end() + next_service.start() if next_service else len(contents)
    return contents[start.start() : end]


def test_dockerfile_embeds_no_init_so_the_launcher_owns_it() -> None:
    """The image must not embed an init of its own."""
    instructions = _instructions(DOCKERFILE)
    assert "tini" not in instructions, (
        "the image must not embed an init; the launcher provides it "
        "(docker run --init / compose init: true)"
    )
    entrypoint = re.search(r"^ENTRYPOINT\s+\[(.+)\]$", instructions, re.MULTILINE)
    assert entrypoint, "Dockerfile must declare an exec-form ENTRYPOINT"
    assert "tini" not in entrypoint.group(1)


def test_compose_declares_the_single_init() -> None:
    """The launcher side of the contract: exactly one init, owned by Compose."""
    service = _service_block(
        COMPOSE.read_text(encoding="utf-8"), "percival-notes"
    )
    assert "init: true" in service, (
        "the compose service must declare init: true so the launcher owns "
        "the init layer and the container stops cleanly on SIGTERM"
    )


def test_dockerfile_runs_as_non_root() -> None:
    """The image must not start as root under a plain ``docker run``."""
    matches = re.findall(r"^USER\s+(\S+)", _instructions(DOCKERFILE), re.MULTILINE)
    assert matches, "Dockerfile must declare a USER directive"
    user = matches[-1]
    assert not user.split(":")[0].isdigit() or int(user.split(":")[0]) != 0, (
        f"the runtime stage must not run as root, got USER {user}"
    )
    assert user == "65532:65532", (
        f"the image user must stay 65532:65532 so the vault mount keeps "
        f"its documented owner, got USER {user}"
    )


def test_stdio_service_has_no_http_surface() -> None:
    """stdio transport: stdin in, JSON-RPC out — no ports, no healthcheck."""
    service = _service_block(
        COMPOSE.read_text(encoding="utf-8"), "percival-notes"
    )
    assert "stdin_open: true" in service
    assert "tty: false" in service
    assert "ports:" not in service
    assert "healthcheck:" not in service


def test_readme_documents_the_ripgrep_version_the_image_installs() -> None:
    """F-014: the README must not advertise a ripgrep version the image lacks."""
    pinned = re.search(r"ripgrep=(\d+\.\d+\.\d+)", _runtime_instructions())
    assert pinned, "Dockerfile must pin an explicit ripgrep version"
    version = pinned.group(1)
    readme = README.read_text(encoding="utf-8")
    assert version in readme, (
        f"README must state the ripgrep version the image installs ({version})"
    )
    mentioned = set(
        re.findall(r"ripgrep\D{0,40}(\d+\.\d+\.\d+)", readme, re.IGNORECASE)
    )
    stale = mentioned - {version}
    assert not stale, (
        f"README mentions ripgrep version(s) {sorted(stale)} that the image "
        f"does not install; the pinned version is {version}"
    )


def test_image_drops_the_package_manager_and_keeps_the_dpkg_inventory() -> None:
    """F-016: no apt/dpkg executables in the runtime; the dpkg DB stays for SBOM."""
    removed = _removed_paths()
    for binary in ("/usr/bin/apt", "/usr/bin/apt-get", "/usr/bin/dpkg"):
        assert binary in removed, (
            f"{binary} must be removed from the runtime image"
        )
    assert "/var/lib/dpkg/status" not in removed, (
        "the dpkg status database must stay so SBOM and scanners can inventory "
        "the installed packages"
    )
    assert "chmod u-s,g-s" in _runtime_instructions(), (
        "setuid/setgid bits must be cleared on the remaining privileged binaries"
    )
