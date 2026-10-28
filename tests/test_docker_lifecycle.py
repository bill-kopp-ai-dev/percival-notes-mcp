"""A-004: one owner, one init — the launcher supplies the init layer.

The image embeds no init, so `docker run --init` (or Compose `init: true`)
must supply exactly one. The contract (S2-C01) keeps a single supervisor per
container: an init inside the image would stack a second supervision layer on
top of the launcher's own and blur who answers SIGTERM.

Measured on the candidate image (2026-10-28), with a writable tmpfs vault:

* with `--init`: `docker stop -t 10` returns in ~0.10 s, exit code 143;
* without `--init`: the server still handles SIGTERM as PID 1 and exits in
  ~1.8 s with exit code 0.

The timeout/SIGKILL degradation reported in the stage-1 readiness evidence
(E-022) does not reproduce with this image, because the server installs its
own SIGTERM handler. The init requirement therefore stays as a contract rule
(single supervisor, predictable exit semantics: 143 means "terminated by
SIGTERM"), not as a workaround for a hanging stop.

These checks need a Docker daemon and an image; they are skipped otherwise.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

import pytest

IMAGE = os.environ.get("PERCIVAL_NOTES_TEST_IMAGE", "percival-notes-mcp:stage2-wip")

pytestmark = pytest.mark.skipif(
    not shutil.which("docker"), reason="requires a docker daemon"
)


def _image_available() -> bool:
    probe = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        capture_output=True, text=True, timeout=60, check=False,
    )
    return probe.returncode == 0


requires_image = pytest.mark.skipif(
    not _image_available(), reason=f"image {IMAGE} is not built locally"
)


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=180, check=False
    )


def _stop_time(extra_args: list[str]) -> tuple[float, int]:
    """Start a container with a writable vault, stop it and measure the shutdown."""
    _run("run", "-d", "--name", "notes-lifecycle-probe",
         "--network=none", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev",
         "--user", "65532:65532",
         "--mount", "type=tmpfs,destination=/vault,tmpfs-mode=0777",
         *extra_args, IMAGE)
    time.sleep(1.0)
    started = time.monotonic()
    _run("stop", "-t", "10", "notes-lifecycle-probe")
    elapsed = time.monotonic() - started
    inspect = _run("inspect", "--format", "{{.State.ExitCode}}", "notes-lifecycle-probe")
    _run("rm", "-f", "notes-lifecycle-probe")
    return elapsed, int(inspect.stdout.strip() or 0)


@requires_image
def test_image_embeds_no_init_process() -> None:
    """No tini/dumb-init binary or entrypoint inside the image."""
    listing = _run("run", "--rm", "--entrypoint", "sh", IMAGE, "-c",
                   "ls /sbin /usr/sbin /usr/bin 2>/dev/null | grep -Ei 'tini|dumb-init' || true")
    assert listing.stdout.strip() == ""
    entrypoint = _run("image", "inspect", "--format", "{{json .Config.Entrypoint}}", IMAGE)
    assert "tini" not in entrypoint.stdout
    assert "dumb-init" not in entrypoint.stdout


@requires_image
def test_stop_with_launcher_init_is_prompt_and_predictable() -> None:
    """With the launcher's init, `docker stop` returns in well under a second."""
    elapsed, exit_code = _stop_time(["--init"])
    assert elapsed < 1.0, f"docker stop took {elapsed:.2f}s with --init"
    assert exit_code == 143, f"expected SIGTERM exit 143, got {exit_code}"


@requires_image
def test_stop_without_init_still_exits_but_with_a_different_code() -> None:
    """Without an init the server exits on SIGTERM, but not with SIGTERM semantics."""
    elapsed, exit_code = _stop_time([])
    assert elapsed < 10.0, f"docker stop should not hit the timeout, took {elapsed:.2f}s"
    assert exit_code != 143, (
        "without the launcher init the container must not report the SIGTERM "
        f"exit code; got {exit_code}"
    )
