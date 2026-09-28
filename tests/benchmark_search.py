"""Reproducible end-to-end search comparison, outside CI.

uv run python tests/benchmark_search.py --sizes 50 250 1000 5000 --repeats 5
"""

import argparse
import hashlib
from dataclasses import replace
import json
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import notes_mcp


def measure(fn, repeats: int):
    expected = fn()  # warmup
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        assert fn() == expected
        samples.append((time.perf_counter() - started) * 1000)
    ordered = sorted(samples)
    return expected, {"min_ms": ordered[0], "median_ms": statistics.median(ordered),
                      "p95_ms": ordered[min(len(ordered) - 1, int(.95 * len(ordered)))],
                      "samples_ms": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[50, 250, 1000, 5000])
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1 or any(n < 1 for n in args.sizes):
        parser.error("sizes and repeats must be positive")
    rg = shutil.which("rg")
    if not rg:
        parser.error("rg is required")
    limits = replace(notes_mcp._load_runtime_limits(),
                     max_search_files=max(args.sizes), max_search_matches=max(args.sizes),
                     operation_timeout_seconds=120.0)
    print(json.dumps({"revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                      "source_sha256": hashlib.sha256(Path(notes_mcp.__file__).read_bytes()).hexdigest(),
                      "benchmark_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "git_status": subprocess.check_output(["git", "status", "--short"], text=True).strip(),
                      "python": sys.version, "rg": subprocess.check_output([rg, "--version"], text=True).splitlines()[0],
                      "hardware": platform.uname()._asdict(), "seed": 1234,
                      "sizes": args.sizes, "repeats": args.repeats,
                      "rg_flags": "--no-config --no-ignore --hidden -a -F -i -l -0 --max-filesize -e -- (inherited /proc/self/fd paths)",
                      "file_size_bytes": "variable, ~100-250", "limits": str(limits)}))
    for size in args.sizes:
        with tempfile.TemporaryDirectory(prefix="okf-bench-") as directory:
            root = Path(directory)
            rng = random.Random(1234)
            for i in range(size):
                marker = "needle" if rng.randrange(10) == 0 else "haystack"
                front = f"---\ntype: Reference\ntitle: {marker} {i}\n---\n" if i % 5 else ""
                body = f"# Note {i}\n{marker} café\n"
                (root / f"{i:05}.md").write_text(front + body, encoding="utf-8")
            for term, body_mode in (("needle", False), ("needle", True),
                                    ("café", True), ("cafe", True)):
                options = dict(root_dir=root, base_dir=root, normalized_query=[term],
                               in_markdown=body_mode, limits=limits)
                legacy, legacy_times = measure(lambda: notes_mcp._search_notes(**options), args.repeats)
                current, current_times = measure(lambda: notes_mcp._search_notes_rg(**options), args.repeats)
                if legacy != current:
                    raise AssertionError(f"search mismatch size={size} term={term!r} body={body_mode}")
                print(json.dumps({"files": size, "term": term, "in_markdown": body_mode,
                                  "matches": len(current), "legacy": legacy_times, "rg": current_times}))


if __name__ == "__main__":
    main()
