"""Resolve the exact wheel set an offline build needs, and verify it locally.

The executor recipe for this product builds with ``--network none``, so the
image build cannot reach PyPI. This script turns the two lock files into an
exact, verifiable wheelhouse manifest:

``plan``
    Reads ``uv.lock`` and ``uv-bootstrap-requirements.lock``, evaluates the
    dependency markers for one target platform, selects the single wheel that
    matches that platform for every package, and writes a manifest with the
    file name, URL and SHA-256 of each artifact. Sizes come from PyPI and are
    informational; the hashes are the contract.

``verify``
    Checks a local wheelhouse directory against a manifest: every file must
    exist and its SHA-256 must match. This is the step the offline build runs
    before installing anything.

Both subcommands are offline except for the optional size lookup in ``plan``,
which is skipped with ``--no-sizes``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

TARGETS = {
    "linux/amd64": {
        "sys_platform": "linux",
        "platform_system": "Linux",
        "platform_machine": "AMD64",
        "python_full_version": "3.12.15",
        "python_version": "3.12",
        "platform_python_implementation": "CPython",
        "implementation_name": "cpython",
        "implementation_version": "3.12.15",
        "os_name": "posix",
    },
}

COMPARISONS = {
    "==": lambda left, right: left == right,
    "!=": lambda left, right: left != right,
    "<=": lambda left, right: left <= right,
    ">=": lambda left, right: left >= right,
    "<": lambda left, right: left < right,
    ">": lambda left, right: left > right,
    "in": lambda left, right: left in right,
    "not in": lambda left, right: left not in right,
}

MARKER_VARIABLE = re.compile(r"\b([a-z_]+)\b")


@dataclass(frozen=True)
class Artifact:
    name: str
    version: str
    filename: str
    url: str
    sha256: str
    size: int | None = None

    def as_dict(self) -> dict[str, object]:
        entry: dict[str, object] = {
            "name": self.name,
            "version": self.version,
            "filename": self.filename,
            "url": self.url,
            "sha256": self.sha256,
        }
        if self.size is not None:
            entry["size"] = self.size
        return entry


def evaluate_marker(marker: str, environment: dict[str, str]) -> bool:
    """Evaluate the PEP 508 marker subset that appears in the lock files.

    Unsupported constructs fail loudly: a marker that cannot be evaluated
    must never be silently treated as true or false.
    """
    for clause in re.split(r"\bor\b", marker):
        if not _evaluate_clause(clause, environment):
            return False
    return True


def _evaluate_clause(clause: str, environment: dict[str, str]) -> bool:
    parts = [part.strip() for part in re.split(r"\band\b", clause) if part.strip()]
    if not parts:
        raise SystemExit(f"unsupported marker clause: {clause!r}")
    result = True
    for part in parts:
        negated = part.startswith("not ")
        if negated:
            part = part[4:].strip()
        match = re.fullmatch(r"([a-z_]+)\s*(not in|==|!=|<=|>=|<|>)\s*(.+)", part)
        if not match:
            raise SystemExit(f"unsupported marker clause: {part!r}")
        variable, operator, raw_value = match.groups()
        if variable not in environment:
            raise SystemExit(f"unsupported marker variable: {variable!r}")
        value = raw_value.strip()
        if not (value.startswith("'") and value.endswith("'")):
            raise SystemExit(f"unsupported marker value: {value!r}")
        compared = environment[variable]
        right = value[1:-1]
        if operator in ("in", "not in"):
            left, right = compared, right
        else:
            left = compared
        outcome = COMPARISONS[operator](left, right)
        result = result and (not outcome if negated else outcome)
    return result


def wheel_is_for_target(filename: str, environment: dict[str, str]) -> bool:
    """Return whether a wheel filename matches the target platform."""
    if not filename.endswith(".whl"):
        return False
    parts = filename[: -len(".whl")].split("-")
    if len(parts) < 3:
        return False
    python_tag, abi_tag, platform_tag = parts[-3], parts[-2], parts[-1]
    if "win" in platform_tag or "macos" in platform_tag or "musl" in platform_tag:
        return False
    if platform_tag != "any" and not platform_tag.endswith("x86_64"):
        return False
    interpreter = environment["python_full_version"]
    if python_tag in ("py3", "py2.py3"):
        return True
    if python_tag.startswith("cp"):
        wanted = "cp" + "".join(interpreter.split(".")[:2])
        if abi_tag == "abi3":
            # An abi3 wheel is forward compatible: it works on any newer
            # CPython of the same major version.
            if int(python_tag[2:]) > int(wanted[2:]):
                return False
        elif python_tag != wanted:
            return False
    if abi_tag in ("none", "abi3"):
        return True
    wanted_abi = "cp" + "".join(interpreter.split(".")[:2])
    return abi_tag == wanted_abi


def runtime_closure(lock: dict[str, object], environment: dict[str, str]) -> list[str]:
    """Return the package names installed for the target platform."""
    packages = {package["name"]: package for package in lock["package"]}
    root = packages.get("percival-notes-mcp")
    if root is None:
        raise SystemExit("uv.lock does not contain the project package")
    resolved: dict[str, bool] = {}

    def visit(name: str, extras: tuple[str, ...] = ()) -> None:
        key = f"{name}[{','.join(sorted(extras))}]"
        if key in resolved:
            return
        resolved[key] = True
        package = packages.get(name)
        if package is None:
            raise SystemExit(f"uv.lock does not contain package {name!r}")
        for dependency in package.get("dependencies", []):
            marker = dependency.get("marker")
            if marker and not evaluate_marker(marker, environment):
                continue
            visit(dependency["name"], tuple(dependency.get("extra", [])))
        for extra in extras:
            for entry in package.get("optional-dependencies", {}).get(extra, []):
                marker = entry.get("marker")
                if marker and not evaluate_marker(marker, environment):
                    continue
                visit(entry["name"], tuple(entry.get("extra", [])))

    for dependency in root.get("dependencies", []):
        marker = dependency.get("marker")
        if marker and not evaluate_marker(marker, environment):
            continue
        visit(dependency["name"], tuple(dependency.get("extra", [])))
    return sorted({key.split("[", 1)[0] for key in resolved})


def wheel_rank(filename: str) -> tuple[int, int]:
    """Rank compatible wheels: broadest glibc first, then the newest abi3 tag."""
    parts = filename[: -len(".whl")].split("-")
    python_tag, platform_tag = parts[-3], parts[-1]
    glibc = 0
    for match in re.finditer(r"manylinux_?(\d+)_(\d+)_x86_64", platform_tag):
        glibc = max(glibc, int(match.group(1)) * 100 + int(match.group(2)))
    minor = int(python_tag[2:]) if python_tag.startswith("cp") else 0
    return (glibc, -minor)


def select_wheel(
    name: str, version: str, package: dict[str, object], environment: dict[str, str]
) -> Artifact:
    candidates = [
        wheel
        for wheel in package.get("wheels", [])
        if wheel_is_for_target(wheel["url"].rsplit("/", 1)[-1], environment)
    ]
    if not candidates:
        raise SystemExit(
            f"no wheel for {name} {version} matches the target platform; the "
            "offline build would need an sdist and a build toolchain"
        )
    if len(candidates) > 1:
        ranked = sorted(
            candidates, key=lambda wheel: wheel_rank(wheel["url"].rsplit("/", 1)[-1])
        )
        best = wheel_rank(ranked[0]["url"].rsplit("/", 1)[-1])
        if wheel_rank(ranked[1]["url"].rsplit("/", 1)[-1]) == best:
            names = sorted(candidate["url"].rsplit("/", 1)[-1] for candidate in candidates)
            raise SystemExit(f"ambiguous wheels for {name} {version}: {names}")
        candidates = [ranked[0]]
    wheel = candidates[0]
    filename = wheel["url"].rsplit("/", 1)[-1]
    return Artifact(
        name=name,
        version=version,
        filename=filename,
        url=wheel["url"],
        sha256=wheel["hash"].removeprefix("sha256:"),
        size=int(wheel["size"]) if "size" in wheel else None,
    )


def locked_artifacts(
    lock_path: Path, environment: dict[str, str], label: str
) -> list[Artifact]:
    """Resolve a hash-pinned requirements file into platform wheels."""
    text = lock_path.read_text(encoding="utf-8").replace("\\\n", " ")
    entries: list[tuple[str, str, set[str]]] = []
    pattern = re.compile(
        r"^([A-Za-z0-9._-]+)==([A-Za-z0-9._-]+)((?:\s+--hash=sha256:[a-f0-9]{64})+)\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        name, version, hash_block = match.groups()
        hashes = set(re.findall(r"--hash=sha256:([a-f0-9]{64})", hash_block))
        if not hashes:
            raise SystemExit(f"bootstrap requirement {name}=={version} has no hash")
        entries.append((name, version, hashes))
    if not entries:
        raise SystemExit(f"no pinned requirements found in {lock_path}")

    artifacts: list[Artifact] = []
    for name, version, expected in entries:
        release = pypi_release(name, version)
        candidates = [
            entry
            for entry in release["urls"]
            if wheel_is_for_target(entry["filename"], environment)
        ]
        if not candidates:
            raise SystemExit(f"no {label} wheel for {name} {version} matches the target")
        if len(candidates) > 1:
            raise SystemExit(f"ambiguous {label} wheels for {name} {version}")
        entry = candidates[0]
        digest = entry["digests"]["sha256"]
        if digest not in expected:
            raise SystemExit(
                f"bootstrap wheel {entry['filename']} hash {digest} is not in the lock"
            )
        artifacts.append(
            Artifact(
                name=name,
                version=version,
                filename=entry["filename"],
                url=entry["url"],
                sha256=digest,
                size=entry["size"],
            )
        )
    return artifacts


def pypi_release(name: str, version: str) -> dict[str, object]:
    """Return the PyPI metadata for one release."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return json.load(response)
    except urllib.error.URLError as error:
        raise SystemExit(f"pypi metadata for {name} {version} is unavailable: {error}")


def build_manifest(args: argparse.Namespace) -> dict[str, object]:
    environment = TARGETS[args.target]
    lock = tomllib.loads(args.lock.read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in lock["package"]}
    artifacts: list[Artifact] = []
    for name in runtime_closure(lock, environment):
        package = packages[name]
        artifacts.append(select_wheel(name, package["version"], package, environment))
    bootstrap = locked_artifacts(args.bootstrap_lock, environment, "bootstrap")
    build = locked_artifacts(args.build_lock, environment, "build backend")
    manifest = {
        "schemaVersion": 1,
        "target": {"platform": args.target, **environment},
        "bootstrap": [artifact.as_dict() for artifact in bootstrap],
        "runtime": [artifact.as_dict() for artifact in artifacts],
        "build": [artifact.as_dict() for artifact in build],
        "totals": {
            "bootstrapPackages": len(bootstrap),
            "runtimePackages": len(artifacts),
            "buildPackages": len(build),
            "bytes": sum(
                artifact.size or 0 for artifact in [*bootstrap, *artifacts, *build]
            ),
        },
    }
    return manifest


def write_manifest(manifest: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_wheelhouse(manifest: dict[str, object], wheelhouse: Path) -> int:
    entries = [*manifest["bootstrap"], *manifest["runtime"], *manifest.get("build", [])]
    missing: list[str] = []
    mismatched: list[str] = []
    for entry in entries:
        path = wheelhouse / str(entry["filename"])
        if not path.is_file():
            missing.append(str(entry["filename"]))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            mismatched.append(str(entry["filename"]))
    for filename in missing:
        print(f"missing: {filename}")
    for filename in mismatched:
        print(f"hash mismatch: {filename}")
    if missing or mismatched:
        print(
            f"wheelhouse verification failed: {len(missing)} missing, "
            f"{len(mismatched)} mismatched of {len(entries)} artifacts"
        )
        return 1
    print(f"wheelhouse verified: {len(entries)} artifacts match the manifest")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="resolve the wheel set for one target")
    plan.add_argument("--target", default="linux/amd64", choices=sorted(TARGETS))
    plan.add_argument("--lock", type=Path, default=Path("uv.lock"))
    plan.add_argument(
        "--bootstrap-lock", type=Path, default=Path("uv-bootstrap-requirements.lock")
    )
    plan.add_argument(
        "--build-lock", type=Path, default=Path("uv-build-requirements.lock")
    )
    plan.add_argument("--output", type=Path, default=Path("vendor/wheelhouse-manifest.json"))
    verify = subparsers.add_parser("verify", help="check a wheelhouse against a manifest")
    verify.add_argument("--manifest", type=Path, default=Path("vendor/wheelhouse-manifest.json"))
    verify.add_argument("--wheelhouse", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "plan":
        manifest = build_manifest(args)
        write_manifest(manifest, args.output)
        totals = manifest["totals"]
        print(
            f"manifest written to {args.output}: {totals['runtimePackages']} runtime, "
            f"{totals['bootstrapPackages']} bootstrap and {totals['buildPackages']} "
            f"build-backend artifacts"
        )
        return
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sys.exit(verify_wheelhouse(manifest, args.wheelhouse))


if __name__ == "__main__":
    main()
