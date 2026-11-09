"""Fetch the wheelhouse artifacts and verify them against the manifest.

Runs inside the wheelhouse base image build, which is the one build that
still has network access. Every artifact is verified against the SHA-256
recorded in the manifest before it is stored, and a requirements file with the
same hashes is written so the offline build can install with
``--require-hashes --no-index``.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

MANIFEST = pathlib.Path("/wheels/manifest.json")
WHEELS = pathlib.Path("/wheels")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = [
        *manifest["bootstrap"],
        *manifest["runtime"],
        *manifest.get("build", []),
    ]
    requirements: list[str] = []
    for entry in entries:
        with urllib.request.urlopen(entry["url"], timeout=300) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"hash mismatch for {entry['filename']}: {digest}")
        (WHEELS / entry["filename"]).write_bytes(data)
        requirements.append(
            f"{entry['name']}=={entry['version']} --hash=sha256:{entry['sha256']}"
        )
    (WHEELS / "requirements.txt").write_text("\n".join(requirements) + "\n", encoding="utf-8")
    (WHEELS / "build-requirements.txt").write_text(
        "\n".join(
            f"{entry['name']}=={entry['version']} --hash=sha256:{entry['sha256']}"
            for entry in manifest.get("build", [])
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"stored {len(requirements)} wheels")


if __name__ == "__main__":
    main()
