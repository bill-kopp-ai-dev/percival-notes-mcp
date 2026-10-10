import os
import sys
from pathlib import Path

import pytest

import docker_entrypoint


def test_entrypoint_uses_configured_mount(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = tmp_path / "isolated-vault"
    vault.mkdir()
    monkeypatch.setenv("PERCIVAL_NOTES_VAULT_PATH", str(vault))
    monkeypatch.setattr(sys, "argv", ["docker_entrypoint.py"])
    monkeypatch.setattr(Path, "is_mount", lambda self: self == vault)
    monkeypatch.setattr(os, "access", lambda *_: True)
    captured: list[object] = []
    monkeypatch.setattr(os, "execv", lambda *args: captured.extend(args))

    docker_entrypoint.main()

    assert captured == ["/opt/venv/bin/percival-notes-mcp", ["percival-notes-mcp", str(vault)]]


@pytest.mark.parametrize("value", ["relative", "/tmp/../escape"])
def test_entrypoint_rejects_relative_or_traversing_vault(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERCIVAL_NOTES_VAULT_PATH", value)
    monkeypatch.setattr(sys, "argv", ["docker_entrypoint.py"])

    with pytest.raises(SystemExit, match="absolute path"):
        docker_entrypoint.main()
