"""Opt-in OpenCode host discovery with an isolated config and dummy Docker vault."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    assert shutil.which("opencode") and shutil.which("docker")
    with tempfile.TemporaryDirectory(prefix="notes-opencode-") as directory:
        root = Path(directory)
        vault = root / "vault"
        vault.mkdir()
        config = {"$schema": "https://opencode.ai/config.json", "mcp": {
            "percival-notes": {"type": "local", "enabled": True, "timeout": 30000,
                               "command": ["docker", "run", "--rm", "-i", "--read-only",
                                           "--tmpfs", "/tmp:rw,nosuid,nodev", "--network", "none",
                                           "--user", f"{os.getuid()}:{os.getgid()}", "--mount",
                                           f"type=bind,src={vault},dst=/vault",
                                           "percival-notes-mcp:docker-test"]}}}
        # Keep both OpenCode state and inherited configuration out of the operator profile.
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("OPENCODE_") and key != "XDG_CONFIG_HOME"}
        env.update(HOME=str(root), OPENCODE_PURE="1",
                   OPENCODE_CONFIG_CONTENT=json.dumps(config))
        for name in ("CONFIG", "DATA", "CACHE", "STATE"):
            path = root / name.lower()
            path.mkdir()
            env[f"XDG_{name}_HOME"] = str(path)
        result = subprocess.run(["opencode", "mcp", "list"], cwd=root, env=env,
                                capture_output=True, text=True, timeout=60, check=False)
        assert result.returncode == 0, result
        plain_output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
        assert any("percival-notes" in line and "connected" in line.lower()
                   for line in plain_output.splitlines()), result
        assert list(vault.iterdir()) == [], "MCP discovery must not write notes"
    print("OpenCode host connected to Docker MCP image with isolated dummy vault")


if __name__ == "__main__":
    main()
