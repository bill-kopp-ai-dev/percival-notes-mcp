# Search characterization (unreleased working tree)

Run on 2026-09-28: `uv run python tests/benchmark_search.py --sizes 50 250 1000 5000 --repeats 3` from the repository root.

Python 3.12.14, ripgrep 15.2.0, Linux x86_64 (Omarchy 7.2.5-3), HEAD `f0f1bef` **with uncommitted refactor**. Source SHA-256: `2bca3b86c8f4aa1214c0f2f27970f44897e3e8b0231d94b3fa2a32d4a8e0f490`; benchmark script SHA-256: `5bc8920857ed9b48eb986e923af24f204449b8b977ff9e2baa620e2b2f829b88`. Generator: deterministic seed 1234, ~100-250 bytes/file, one `.md` per note, 80% with frontmatter, 10% marker distribution, body contains accented `café`. Both implementations ran against the same temporary vault, warmup plus three measurements, parity asserted before reporting. Modes: YAML only and YAML+body. Flags: `--no-config --no-ignore --hidden -a -F -i -l -0 --max-filesize -e ... -- /proc/self/fd/<inherited-fd>`. Wall-clock end-to-end, milliseconds; medians rounded to one decimal. With only three samples, these are preliminary observations rather than stable p95 estimates.

Each triplet is min / median / empirical p95 (maximum of three samples), in ms. No run failed or was ignored.

| Files | Query / mode | Matches | Walker (ms) | rg-backed (ms) |
|---:|---|---:|---:|---:|
| 50 | needle / YAML | 7 | 11.2 / 11.4 / 11.4 | 22.4 / 23.3 / 23.8 |
| 50 | needle / YAML+body | 9 | 11.3 / 11.4 / 11.7 | 22.8 / 23.4 / 23.6 |
| 50 | café / YAML+body | 50 | 11.6 / 12.5 / 12.9 | 21.8 / 21.8 / 22.7 |
| 50 | cafe / YAML+body | 0 | 11.7 / 11.8 / 12.1 | 24.4 / 25.6 / 25.9 |
| 250 | needle / YAML | 21 | 57.1 / 58.2 / 58.6 | 104.0 / 105.1 / 106.2 |
| 250 | needle / YAML+body | 26 | 57.2 / 57.3 / 59.0 | 102.7 / 104.6 / 106.1 |
| 250 | café / YAML+body | 250 | 59.5 / 59.5 / 59.7 | 92.4 / 92.9 / 100.0 |
| 250 | cafe / YAML+body | 0 | 52.7 / 53.1 / 56.1 | 105.7 / 108.7 / 109.3 |
| 1000 | needle / YAML | 75 | 225.9 / 232.4 / 232.7 | 405.9 / 414.4 / 420.1 |
| 1000 | needle / YAML+body | 90 | 227.2 / 234.1 / 240.0 | 412.0 / 415.2 / 418.7 |
| 1000 | café / YAML+body | 1000 | 228.0 / 229.6 / 234.0 | 360.5 / 361.1 / 361.3 |
| 1000 | cafe / YAML+body | 0 | 223.5 / 229.0 / 230.9 | 418.3 / 420.6 / 423.9 |
| 5000 | needle / YAML | 388 | 1069.7 / 1073.3 / 1085.0 | 1722.6 / 1912.2 / 1925.5 |
| 5000 | needle / YAML+body | 483 | 1080.9 / 1173.9 / 1178.9 | 1708.1 / 1728.8 / 1791.2 |
| 5000 | café / YAML+body | 5000 | 964.7 / 966.2 / 968.4 | 1597.6 / 1604.0 / 1878.5 |
| 5000 | cafe / YAML+body | 0 | 961.9 / 966.8 / 967.4 | 1734.7 / 1920.4 / 2044.8 |

**Result:** parity held in this synthetic corpus, but the bounded/parity-preserving rg wrapper was slower than the walker here. Explicit file enumeration, anchored path checks, batches, output handling and Unicode fallback dominate tiny-file workloads. No latency target is agreed; do not claim speedup. Re-run after any optimization, preferably with a representative real vault (with permission), and record revision/hash, environment and raw samples from the script output. Empty-vault, hidden/ignored, symlink, oversized, literal regex and Unicode edge cases are verified in tests, not timed in this table.
