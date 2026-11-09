"""Contract checks for the offline image build.

The executor recipe builds this product with ``--network none``. That only
works if every dependency is already local, so these checks fail the build
when the offline path drifts:

* the wheelhouse manifest covers exactly the runtime closure of ``uv.lock``
  for the target platform, and every artifact hash comes from the lock files;
* the offline Dockerfile has no instruction that would reach the network;
* the base images that carry the Debian runtime and the wheels pin every
  package to an exact version and every base image by digest.

The offline variant stays *inactive* until the operator builds the two base
images and their digests replace the placeholders. While it is inactive, the
checks assert that it cannot be activated by accident: the placeholders are
still placeholders and the recipe still points at the networked Dockerfile.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
OFFLINE_DOCKERFILE = REPO_ROOT / "Dockerfile.offline"
RUNTIME_BASE = REPO_ROOT / "docker" / "offline-runtime.Dockerfile"
WHEELHOUSE_BASE = REPO_ROOT / "docker" / "offline-wheelhouse.Dockerfile"
MANIFEST = REPO_ROOT / "vendor" / "wheelhouse-manifest.json"
LOCK = REPO_ROOT / "uv.lock"
BOOTSTRAP_LOCK = REPO_ROOT / "uv-bootstrap-requirements.lock"
BUILD_LOCK = REPO_ROOT / "uv-build-requirements.lock"
PLACEHOLDER = "scratch"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _instructions(path: Path) -> list[str]:
    """Return the logical instructions of a Dockerfile, continuations joined."""
    text = path.read_text(encoding="utf-8")
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    return [
        line.strip()
        for line in joined.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _load_tool():
    """Import the wheelhouse tool, whose file name is not a module name."""
    import importlib.util

    path = REPO_ROOT / "scripts" / "offline-wheelhouse.py"
    spec = importlib.util.spec_from_file_location("offline_wheelhouse", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["offline_wheelhouse"] = module
    spec.loader.exec_module(module)
    return module


def _locked_hashes(path: Path) -> set[str]:
    return set(
        re.findall(r"--hash=sha256:([a-f0-9]{64})", path.read_text(encoding="utf-8"))
    )


def test_manifest_covers_the_locked_runtime_closure() -> None:
    """Every runtime package of the lock is in the manifest, and only those."""
    offline_wheelhouse = _load_tool()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    closure = offline_wheelhouse.runtime_closure(
        lock, offline_wheelhouse.TARGETS["linux/amd64"]
    )
    assert manifest["target"]["platform"] == "linux/amd64"
    manifest_names = {entry["name"] for entry in manifest["runtime"]}
    assert manifest_names == set(closure), (
        "the wheelhouse manifest drifted from the locked runtime closure: "
        f"missing {sorted(set(closure) - manifest_names)}, "
        f"extra {sorted(manifest_names - set(closure))}"
    )


def test_manifest_hashes_come_from_the_lock_files() -> None:
    """No artifact hash is invented: every one is recorded in a lock file."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime_hashes = set()
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    for package in lock["package"]:
        for wheel in package.get("wheels", []):
            runtime_hashes.add(wheel["hash"].removeprefix("sha256:"))
    for entry in manifest["runtime"]:
        assert entry["sha256"] in runtime_hashes, (
            f"{entry['filename']} hash is not recorded in uv.lock"
        )
    locked = _locked_hashes(BOOTSTRAP_LOCK) | _locked_hashes(BUILD_LOCK)
    for entry in [*manifest["bootstrap"], *manifest.get("build", [])]:
        assert entry["sha256"] in locked, (
            f"{entry['filename']} hash is not recorded in the bootstrap or build lock"
        )


def test_offline_dockerfile_has_no_network_instruction() -> None:
    """The offline build must resolve everything from local artifacts."""
    instructions = _instructions(OFFLINE_DOCKERFILE)
    body = "\n".join(instructions)
    assert "apt-get" not in body, "the offline image must not run apt"
    assert "uv sync" not in body, "the offline image must not resolve with uv"
    for instruction in instructions:
        if "pip install" not in instruction:
            continue
        assert "--no-index" in instruction, f"pip install without --no-index: {instruction}"
        assert "--find-links" in instruction, (
            f"pip install without --find-links: {instruction}"
        )


def test_offline_variant_is_pinned_or_explicitly_inactive() -> None:
    """The offline path is inert until real base digests replace the placeholders."""
    instructions = _instructions(OFFLINE_DOCKERFILE)
    arguments = dict(re.findall(r"^ARG\s+(\w+)=(\S+)", "\n".join(instructions), re.MULTILINE))
    bases = {
        name: value
        for name, value in arguments.items()
        if name in {"RUNTIME_BASE", "WHEELHOUSE_BASE"}
    }
    assert set(bases) == {"RUNTIME_BASE", "WHEELHOUSE_BASE"}
    active = all(
        re.fullmatch(r"sha256:[a-f0-9]{64}", value) for value in bases.values()
    )
    if active:
        return
    for name, value in bases.items():
        assert value == PLACEHOLDER, (
            f"{name} must be either a digest or the documented placeholder, got {value}"
        )
    project = json.loads(
        (REPO_ROOT / ".positronic" / "project.json").read_text(encoding="utf-8")
    )
    dockerfile = (
        project.get("operations", {}).get("image", {}).get("dockerfile") or "Dockerfile"
    )
    assert dockerfile != "Dockerfile.offline", (
        "the offline variant is still inactive, so the recipe must not point at it"
    )


def test_base_images_pin_every_package_and_base() -> None:
    """The Debian runtime base pins each package version of the snapshot."""
    instructions = _instructions(RUNTIME_BASE)
    body = "\n".join(instructions)
    install = next(
        (instruction for instruction in instructions if "apt-get install" in instruction),
        None,
    )
    assert install, "the runtime base must install its packages explicitly"
    packages = re.findall(r"([a-z0-9][a-z0-9.+-]*)=([^\s\\]+)", install)
    assert packages, "the runtime base must pin every package to an exact version"
    for name, version in packages:
        assert version and not version.endswith(","), (
            f"package {name} is not pinned to an exact version"
        )
    for base in re.findall(r"^FROM\s+(\S+)", body, re.MULTILINE):
        assert re.fullmatch(r"[^@\s]+@sha256:[a-f0-9]{64}", base), (
            f"the runtime base must be digest-pinned, got {base}"
        )
    removals = next(
        (instruction for instruction in instructions if "rm -f " in instruction), ""
    )
    for binary in ("/usr/bin/apt", "/usr/bin/apt-get", "/usr/bin/dpkg"):
        assert binary in removals, f"the runtime base must remove {binary}"
    assert "chmod u-s,g-s" in body


def test_wheelhouse_base_is_digest_pinned() -> None:
    """The wheelhouse base carries the wheels and pins its own base image."""
    body = "\n".join(_instructions(WHEELHOUSE_BASE))
    for base in re.findall(r"^FROM\s+(\S+)", body, re.MULTILINE):
        assert re.fullmatch(r"[^@\s]+@sha256:[a-f0-9]{64}", base), (
            f"the wheelhouse base must be digest-pinned, got {base}"
        )
    assert "manifest.json" in body
    assert "hash mismatch" in body


def test_offline_variant_keeps_the_runtime_identity() -> None:
    """Same user and entrypoint as the networked reference."""
    reference = "\n".join(_instructions(DOCKERFILE))
    offline = "\n".join(_instructions(OFFLINE_DOCKERFILE))
    assert "USER 65532:65532" in offline
    assert 'ENTRYPOINT ["python", "/app/docker_entrypoint.py"]' in offline
    assert "USER 65532:65532" in reference
    assert "chown 65532:65532 /vault" in reference
