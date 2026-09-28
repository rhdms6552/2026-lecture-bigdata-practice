# Implementation and reproduction

## Task 1

`BloomFilter` packs bits into a bytearray and uses seeded SHAKE-256 output as k 64-bit hash values. It never clears bits. Its prediction is `(1 - exp(-k*n/m))**k`.

FM retains 64 trailing-zero maxima. It reads the same 64-bit hashes byte by byte to avoid allocating many temporary integers under tracemalloc. Eight interleaved groups each contain eight estimates; the result averages their medians. This robust combining rule suppresses extreme maxima without claiming a probabilistic factor-of-two guarantee for every possible stream. `sketch_analysis.json` records the arithmetic mean, median, chosen rule, and a ten-seed check. Evaluation code may retain a small reference dataset; the sketches do not.

Reservoir sampling uses Algorithm R. At stream position n, it chooses an integer uniformly from 0 through n-1 and replaces a slot only if the integer is below k. For an item already in the sample, survival at that step is `1 - 1/n`; multiplying the later survival probabilities gives final inclusion probability k/N.

## Task 2

`task2_limits.py` retains the original stream and measurement functions. It now saves each completed row immediately and prints progress after exact counting, so a later interruption cannot discard completed measurements. `limits.md` documents the measured machine, concurrent load, all four sizes, accuracy, growth rates, and the practical time limit. Timings use tracemalloc and are not uninstrumented production speed measurements.

## Task 3

`YourFilter` uses seven hashes, a packed bytearray, and `__slots__`. The 10,000-byte persistent per-filter budget includes the instance object, seed bytes, bytearray object, and its allocated buffer. On this CPython build the payload is 9,859 bytes (78,872 bits), and the remaining 141 bytes hold metadata. `memory_bits()` sums these sizes with `sys.getsizeof`. There are no stored input items, extra tables, or per-instance hash objects. Shared interpreter/code memory and transient query execution space are outside this resident-state accounting.

With 78,872 usable bits and 8,000 inserted items, the optimum is k = 6.834, rounded to 7. The predicted rate is 0.8774%; the measured rate is 1,757 / 200,000 = 0.8785%, with no false negatives. The ideal continuous-k floor with ten payload bits per item is 0.8193%, so metadata accounts for much of the difference. The unmodified baseline reports 80,000 logical bits even though its bytearray stores a byte per logical bit; the improved implementation stays within 80,000 bits including its resident metadata.

## Commands

Run from `w04-stream/` with Python 3 (`python` on this Windows machine):

```text
python task1_sketches.py --verify
python task2_limits.py --sizes 100000,400000,1600000,6400000
python analyze_sketches.py
python bench.py --yours
python write_report.py --machine out/machine_snapshot.json
python test_tasks.py
python ../check.py w04
```

Save the benchmark output to `out/bench.txt` before running `write_report.py`. The machine snapshot is the recorded environment for this submission; replace it with a fresh snapshot when measuring a different machine. New task-2 runs append to `out/limits.json`. `bench.py`, `test_tasks.py`, and `check.py` are unchanged.
