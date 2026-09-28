# Task 2: measured memory and practical limit

## Machine and method

- CPU: 12th Gen Intel(R) Core(TM) i7-1260P; OS: Microsoft Windows 11 Home (Windows-10-10.0.26200-SP0); Python 3.11.8.
- Usable RAM: 15.63 GiB; available RAM at the snapshot: 2.75 GiB.
- Other running software: ChatGPT, Memory Compression, MsMpEng, chrome; snapshot: 2026-09-28T09:45:11.1316041+09:00.
- A separate Codex task ran Python stream measurements concurrently for part of this experiment; wall times include that contention.
- Stream: seed 246, n generated strings, key range floor(0.4n). Each method receives a fresh generator with identical contents. True counts come from the measured exact set.
- Memory is peak Python allocations measured by tracemalloc, in decimal MB or bytes. It excludes interpreter, OS, and tracemalloc's own bookkeeping; it is not total process RAM. Timings include generation and tracing overhead on this busy computer.
- FM uses 64 hashes and averages eight group medians. The generator and sketch retain no stream history.

## Results (A1, A3, A5)

| Stream n | True distinct | Exact seconds | Exact peak MB | FM seconds | FM peak bytes | FM estimate | Estimate / truth |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 36,702 | 0.48 | 4.219 | 2.15 | 8,601 | 37,888 | 1.032 |
| 400,000 | 146,970 | 6.43 | 12.767 | 20.73 | 8,602 | 212,992 | 1.449 |
| 1,600,000 | 587,625 | 28.27 | 51.349 | 110.94 | 8,602 | 638,976 | 1.087 |
| 6,400,000 | 2,349,909 | 109.18 | 207.087 | 287.92 | 8,603 | 2,293,760 | 0.976 |

## Where I stopped (A2)

The practical stopping size was **6,400,000 items**: exact counting took **109.18 seconds**, exceeding a stated one-minute budget for an interactive experiment, with **207.087 MB** of traced peak allocations. Time became the limiting resource for repeated experiments. This run completed; RAM was not exhausted, so these results do not establish the machine's maximum possible exact set size.

## Growth and accuracy (A4, A5)

Across a 64x increase in n, exact peak memory grew 49.08x (4.219 to 207.087 MB): endpoint log-log slope 0.936, consistent with roughly O(n) memory at this fixed distinct ratio. Set capacity grows in steps and key strings become slightly longer, so the measured multiplier need not equal 64 exactly.

FM peak memory changed 1.00023x (8,601 to 8,603 bytes): endpoint slope 0.00006, effectively O(64) = O(1) in n. The tiny difference includes generator/string and temporary allocation effects; the number of registers stays fixed.

The accuracy ratios were 1.032x, 1.449x, 1.087x, 0.976x. More data does not force this fixed-size sketch toward the truth: its error depends on the hash maxima, and the results do not show a reliable improvement with n. FM saves space but was slower than exact counting in these traced Python runs.

A factor-of-two estimate can support rough traffic sizing or order-of-magnitude capacity planning. It is too imprecise for billing, contractual usage limits, or judging a small change in daily distinct visitors.

## Reproduce

From `w04-stream/`, run `python task2_limits.py --sizes 100000,400000,1600000,6400000`. The script appends completed runs to `out/limits.json`; preserve the existing measurements before rerunning. On systems with a `python3` executable, use that command name. Run `python analyze_sketches.py`, save `python bench.py --yours` to `out/bench.txt`, and run `python write_report.py --machine out/machine_snapshot.json` to rebuild this report from the saved evidence.
