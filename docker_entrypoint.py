"""Fail closed when the container vault is not an explicit mount."""

import os
import sys
from pathlib import Path


def main() -> None:
    vault = Path(os.environ.get("PERCIVAL_NOTES_VAULT_PATH", "/vault"))
    if len(sys.argv) != 1:
        raise SystemExit("Docker entrypoint takes no arguments; mount the vault at /vault")
    if not vault.is_absolute() or ".." in vault.parts:
        raise SystemExit("PERCIVAL_NOTES_VAULT_PATH must be an absolute path without traversal")
    if vault.is_symlink() or not vault.is_dir() or not vault.is_mount():
        raise SystemExit("the configured vault path must be a mounted directory (bind mount or Docker volume)")
    if not os.access(vault, os.R_OK | os.W_OK | os.X_OK):
        raise SystemExit("the configured vault path is not readable and writable by the container user")
    os.execv("/opt/venv/bin/percival-notes-mcp", ["percival-notes-mcp", str(vault)])


if __name__ == "__main__":
    main()
