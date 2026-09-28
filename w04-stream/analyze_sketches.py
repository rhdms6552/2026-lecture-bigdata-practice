"""Reproduce the combining-rule comparison and stream edge checks."""
import json
import math
from pathlib import Path
import random
import statistics

from task1_sketches import (BloomFilter, combine_fm, flajolet_martin,
                            fm_registers, hash_words, reservoir_sample)
from task2_limits import stream
from task3_budget import YourFilter


def main():
    out = Path(__file__).with_name("out")
    out.mkdir(exist_ok=True)
    rng = random.Random(246)
    # This small reference dataset is only for evaluation, never sketch state.
    data = [f"k{rng.randrange(20_000)}" for _ in range(120_000)]
    registers = fm_registers(iter(data))
    estimates = [2 ** r for r in registers]
    result = {
        "true_distinct": len(set(data)),
        "arithmetic_mean": statistics.mean(estimates),
        "median": statistics.median(estimates),
        "mean_of_eight_group_medians": combine_fm(registers),
        "registers": registers,
    }
    result["ratios_by_seed"] = [
        {"seed": s, "ratio": flajolet_martin(stream(10_000, 1, s), seed=s)
         / len(set(stream(10_000, 1, s)))} for s in range(10)
    ]
    assert all(0.5 <= r["ratio"] <= 2 for r in result["ratios_by_seed"])

    # Check that the byte-based fast path preserves full 64-bit hash maxima.
    expected = [-1] * 64
    for item in range(3000):
        for i, word in enumerate(hash_words(item, 64, 246)):
            zeros = (word & -word).bit_length() - 1 if word else 64
            expected[i] = max(expected[i], zeros)
    assert fm_registers(iter(range(3000))) == expected
    assert flajolet_martin(iter(())) == 0
    assert fm_registers(iter(["same"] * 100)) == fm_registers(iter(["same"]))
    assert reservoir_sample(iter(range(3)), 5) == [0, 1, 2]
    assert reservoir_sample(iter(range(20)), 0) == []
    assert len(set(reservoir_sample(iter(range(1000)), 10))) == 10
    for seed in range(5):
        bf = BloomFilter(8192, 5, seed)
        budget = YourFilter(80_000, seed)
        for item in range(800):
            bf.add(item)
            budget.add(item)
        assert all(item in bf and item in budget for item in range(800))
        assert budget.memory_bits() <= 80_000
    budget = YourFilter(80_000)
    payload = len(budget.bits) * 8
    result["budget_filter"] = {
        "payload_bits": payload, "resident_bits": budget.memory_bits(),
        "k": budget.K, "continuous_optimal_k": payload / 8000 * math.log(2),
        "ideal_10_bit_floor": math.exp(-10 * math.log(2) ** 2),
        "predicted_rate_with_metadata": (-math.expm1(-7 * 8000 / payload)) ** 7,
    }
    (out / "sketch_analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Stream edge checks, hash equivalence, and all 10 FM seeds passed.")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
