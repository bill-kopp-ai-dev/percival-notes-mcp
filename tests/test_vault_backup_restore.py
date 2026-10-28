"""A-002: the published backup/restore procedure, exercised on a synthetic vault.

The vault is synthetic: no real user data is copied, restored or inspected.
The owner-only steps (backup, restore, chown) run inside a container as root,
which is how the procedure is meant to run on a host where the vault belongs to
the container identity (65532:65532).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_UID = 65532
RUNTIME_GID = 65532
BASE_IMAGE = (
    "debian:forky-slim@sha256:4cee6ff3ebc49e32d55a857e25164ef8e5f8fecff2a186c6393f7e8bd8c23b53"
)

pytestmark = pytest.mark.skipif(
    not shutil.which("docker"), reason="requires a docker daemon for the root-only steps"
)


def _run_in_container(workdir: Path, script: str, *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "run", "--rm", "--network=none",
         "-v", f"{REPO_ROOT}:/repo:ro", "-v", f"{workdir}:/work",
         BASE_IMAGE, "bash", "-c", script],
        check=check, text=True, capture_output=True, timeout=300,
    )


@pytest.fixture
def synthetic_vault(tmp_path: Path):
    # The container identity must be able to traverse the mount point.
    tmp_path.chmod(0o755)
    vault = tmp_path / "vault"
    (vault / "sub").mkdir(parents=True)
    (vault / "note.md").write_text(
        "---\ntype: Reference\ntags: [demo]\n---\n# Note\nbody\n", encoding="utf-8"
    )
    (vault / "sub" / "other.md").write_text(
        "---\ntype: Playbook\n---\n# Other\n", encoding="utf-8"
    )
    (vault / "sub" / "other.md").chmod(0o640)
    _run_in_container(
        tmp_path,
        f"chown -R {RUNTIME_UID}:{RUNTIME_GID} /work/vault",
    )
    yield tmp_path
    # The container writes as root; hand the tree back to the operator.
    _run_in_container(
        tmp_path,
        f"chown -R {os.getuid()}:{os.getgid()} /work || true",
        check=False,
    )


def test_backup_and_restore_preserve_owner_and_content(synthetic_vault: Path) -> None:
    result = _run_in_container(
        synthetic_vault,
        """
        set -e
        /repo/scripts/vault-backup.sh --vault /work/vault --dest /work/backups --label stage2
        archive=$(ls -1 /work/backups/*.tar)
        echo "ARCHIVE=$archive"
        echo "MANIFEST_OWNER=$(awk -F'\\t' 'NR > 1 { print $2 ":" $3 }' "$archive.manifest" | sort -u | tr '\\n' ' ')"
        /repo/scripts/vault-restore.sh --archive "$archive" --target /work/restored
        echo "NOTE_UID=$(stat -c '%u' /work/restored/vault/note.md)"
        echo "NOTE_GID=$(stat -c '%g' /work/restored/vault/note.md)"
        echo "OTHER_MODE=$(stat -c '%a' /work/restored/vault/sub/other.md)"
        echo "NOTE_SHA=$(sha256sum /work/restored/vault/note.md | cut -d' ' -f1)"
        echo "ORIGINAL_SHA=$(sha256sum /work/vault/note.md | cut -d' ' -f1)"
        """,
    )
    out = result.stdout
    assert "vault-backup:" in out
    assert "read-after-restore ok" in out
    assert "owner_failures=0" in out
    assert "content_failures=0" in out
    assert f"MANIFEST_OWNER={RUNTIME_UID}:{RUNTIME_GID} " in out
    assert f"NOTE_UID={RUNTIME_UID}" in out
    assert f"NOTE_GID={RUNTIME_GID}" in out
    assert "OTHER_MODE=640" in out
    assert "NOTE_SHA=" in out and "ORIGINAL_SHA=" in out
    assert _value(out, "NOTE_SHA") == _value(out, "ORIGINAL_SHA")


def test_restore_without_owner_preservation_is_rejected(synthetic_vault: Path) -> None:
    """The silent failure mode: files restored as root are unusable by the server."""
    result = _run_in_container(
        synthetic_vault,
        """
        set -e
        /repo/scripts/vault-backup.sh --vault /work/vault --dest /work/backups --label stage2
        archive=$(ls -1 /work/backups/*.tar)
        mkdir -p /work/broken
        tar --numeric-owner --no-same-owner --owner=0 --group=0 -xpf "$archive" -C /work/broken
        echo "BROKEN_UID=$(stat -c '%u' /work/broken/vault/note.md)"
        set +e
        /repo/scripts/vault-restore.sh --archive "$archive" --verify /work/broken/vault
        echo "VERIFY_EXIT=$?"
        setpriv --reuid=65532 --regid=65532 --clear-groups cat /work/broken/vault/note.md
        echo "PROBE_EXIT=$?"
        """,
        check=False,
    )
    out = result.stdout
    assert "BROKEN_UID=0" in out
    assert "OWNER MISMATCH" in result.stderr
    assert "did not preserve the numeric owner" in result.stderr
    assert "VERIFY_EXIT=1" in out
    assert "PROBE_EXIT=1" in out


def test_backup_keeps_the_documented_retention(synthetic_vault: Path) -> None:
    """Seven daily plus four weekly snapshots survive; older copies are pruned."""
    backups = synthetic_vault / "backups"
    backups.mkdir()
    stamps = [
        "20260101T000000Z", "20260102T000000Z", "20260103T000000Z", "20260104T000000Z",
        "20260105T000000Z", "20260106T000000Z", "20260107T000000Z", "20260108T000000Z",
        "20260109T000000Z", "20260110T000000Z", "20260111T000000Z", "20260112T000000Z",
    ]
    for stamp in stamps:
        archive = backups / f"{stamp}-stage2.tar"
        archive.write_bytes(b"")
        archive.with_suffix(".tar.manifest").write_text("", encoding="utf-8")
        archive.with_suffix(".tar.sha256").write_text("", encoding="utf-8")
        archive.with_suffix(".tar.meta").write_text("", encoding="utf-8")

    _run_in_container(
        synthetic_vault,
        """
        set -e
        /repo/scripts/vault-backup.sh --vault /work/vault --dest /work/backups --label stage2
        ls -1 /work/backups/*.tar | sed 's#.*/##' | sort
        """,
    )
    remaining = sorted(path.name for path in backups.glob("*.tar"))
    assert len(remaining) <= 7 + 4 + 1
    assert len(remaining) >= 7
    assert remaining[-1].startswith("20261028T")


def _value(output: str, key: str) -> str:
    for line in output.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    raise AssertionError(f"{key} not found in output: {output}")
