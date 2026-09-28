"""Reproducible FM combination and Bloom theory/state measurements."""
import json
import math
import random
import sys
from pathlib import Path

import bench
from task1_sketches import BloomFilter, fm_registers, fm_combinations
from task3_budget import YourFilter, NaiveFilter


def stream():
    rng = random.Random(246)
    for _ in range(120000):
        yield f"k{rng.randrange(20000)}"


def main():
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    true = len(set(stream()))
    trials = []
    for seed in (246, 0, 1, 2, 3, 4):
        maxima, _ = fm_registers(stream(), seed=seed)
        rules = fm_combinations(maxima)
        trials.append({"seed": seed, "true_distinct": true,
                       "estimates": rules,
                       "ratios": {name: value / true for name, value in rules.items()}})
    bf = BloomFilter(8192, 5)
    for i in range(800):
        bf.add(f"item-{i}")
    measured = sum(f"other-{i}" in bf for i in range(20000)) / 20000
    inserted, absent = bench.build()
    result = bench.run(YourFilter, "yours", inserted, absent)
    f = YourFilter(bench.N_BITS)
    baseline = NaiveFilter(bench.N_BITS)
    m = (len(f._state) - 8) * 8
    data = {"fm_trials": trials,
            "task1_bloom": {"predicted": bf.expected_fp_rate(800), "measured": measured},
            "task3": {**result, "n_insert": bench.N_INSERT, "n_query": bench.N_QUERY,
                      "k_opt_ideal": 10 * math.log(2), "k_used": 7,
                      "ideal_floor": math.exp(-10 * math.log(2) ** 2),
                      "ideal_k7": (1 - math.exp(-7 / 10)) ** 7,
                      "payload_bits": m,
                      "actual_prediction": (1 - math.exp(-7 * bench.N_INSERT / m)) ** 7,
                      "retained_bits": f.memory_bits(),
                      "object_bytes": sys.getsizeof(f),
                      "state_allocation_bytes": sys.getsizeof(f._state),
                      "seed_bytes": 8,
                      "baseline_bytearray_allocation_bytes": sys.getsizeof(baseline.bits)}}
    (out / "experiments.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
