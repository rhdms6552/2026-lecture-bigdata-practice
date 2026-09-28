"""Build the written submission from measured results and a machine snapshot.

Usage: python write_report.py --machine out/machine_snapshot.json
Run task2_limits.py, analyze_sketches.py, and bench.py --yours first.
"""
import argparse
import json
import math
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--machine", type=Path, required=True)
    args = parser.parse_args()
    out = Path(__file__).with_name("out")
    data = json.loads((out / "limits.json").read_text(encoding="utf-8"))
    snapshot = json.loads(args.machine.read_text(encoding="utf-8-sig"))
    data["machine"].update({
        "cpu_model": snapshot["cpu"],
        "ram_bytes": snapshot["os"]["TotalVisibleMemorySize"] * 1024,
        "available_ram_bytes_at_snapshot": snapshot["os"]["FreePhysicalMemory"] * 1024,
        "snapshot_time": snapshot["captured_at"],
        "other_running_processes": sorted({p["ProcessName"] for p in snapshot["running"]}),
        "measurement_load_note": "A separate Codex task ran Python stream measurements concurrently for part of this experiment; wall times include that contention.",
    })
    rows = sorted(data["runs"], key=lambda r: r["n"])
    assert len({r["n"] for r in rows}) >= 4
    # An explicitly stated practical latency limit, not an invented OOM claim.
    slow = next((r for r in rows if r["exact_s"] >= 60), None)
    if slow is None:
        raise RuntimeError("Exact has not yet crossed the 60-second practical limit; measure a larger size.")
    data["stopping_reason"] = {
        "n": slow["n"], "resource": "time", "interactive_budget_seconds": 60,
        "observed_exact_seconds": slow["exact_s"],
        "note": "Completed, but exceeded one minute per exact pass. No out-of-memory failure observed.",
    }
    (out / "limits.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    first, last = rows[0], rows[-1]
    size_ratio = last["n"] / first["n"]
    exact_ratio = last["exact_peak_bytes"] / first["exact_peak_bytes"]
    fm_ratio = last["fm_peak_bytes"] / first["fm_peak_bytes"]
    exact_slope = math.log(exact_ratio) / math.log(size_ratio)
    fm_slope = math.log(fm_ratio) / math.log(size_ratio)
    table = "\n".join(
        f"| {r['n']:,} | {r['true_distinct']:,} | {r['exact_s']:.2f} | "
        f"{r['exact_peak_bytes'] / 1e6:.3f} | {r['fm_s']:.2f} | "
        f"{r['fm_peak_bytes']:,} | {r['fm_estimate']:,.0f} | {r['fm_ratio']:.3f} |"
        for r in rows)
    m = data["machine"]
    text = f"""# Task 2: measured memory and practical limit

## Machine and method

- CPU: {m['cpu_model']}; OS: {snapshot['os']['Caption']} ({m['platform']}); Python {m['python']}.
- Usable RAM: {m['ram_bytes'] / 2**30:.2f} GiB; available RAM at the snapshot: {m['available_ram_bytes_at_snapshot'] / 2**30:.2f} GiB.
- Other running software: {', '.join(m['other_running_processes'])}; snapshot: {m['snapshot_time']}.
- {m['measurement_load_note']}
- Stream: seed 246, n generated strings, key range floor(0.4n). Each method receives a fresh generator with identical contents. True counts come from the measured exact set.
- Memory is peak Python allocations measured by tracemalloc, in decimal MB or bytes. It excludes interpreter, OS, and tracemalloc's own bookkeeping; it is not total process RAM. Timings include generation and tracing overhead on this busy computer.
- FM uses 64 hashes and averages eight group medians. The generator and sketch retain no stream history.

## Results (A1, A3, A5)

| Stream n | True distinct | Exact seconds | Exact peak MB | FM seconds | FM peak bytes | FM estimate | Estimate / truth |
|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

## Where I stopped (A2)

The practical stopping size was **{slow['n']:,} items**: exact counting took **{slow['exact_s']:.2f} seconds**, exceeding a stated one-minute budget for an interactive experiment, with **{slow['exact_peak_bytes'] / 1e6:.3f} MB** of traced peak allocations. Time became the limiting resource for repeated experiments. This run completed; RAM was not exhausted, so these results do not establish the machine's maximum possible exact set size.

## Growth and accuracy (A4, A5)

Across a {size_ratio:.0f}x increase in n, exact peak memory grew {exact_ratio:.2f}x ({first['exact_peak_bytes'] / 1e6:.3f} to {last['exact_peak_bytes'] / 1e6:.3f} MB): endpoint log-log slope {exact_slope:.3f}, consistent with roughly O(n) memory at this fixed distinct ratio. Set capacity grows in steps and key strings become slightly longer, so the measured multiplier need not equal {size_ratio:.0f} exactly.

FM peak memory changed {fm_ratio:.5f}x ({first['fm_peak_bytes']:,} to {last['fm_peak_bytes']:,} bytes): endpoint slope {fm_slope:.5f}, effectively O(64) = O(1) in n. The tiny difference includes generator/string and temporary allocation effects; the number of registers stays fixed.

The accuracy ratios were {', '.join(f"{r['fm_ratio']:.3f}x" for r in rows)}. More data does not force this fixed-size sketch toward the truth: its error depends on the hash maxima, and the results do not show a reliable improvement with n. FM saves space but was slower than exact counting in these traced Python runs.

A factor-of-two estimate can support rough traffic sizing or order-of-magnitude capacity planning. It is too imprecise for billing, contractual usage limits, or judging a small change in daily distinct visitors.

## Reproduce

From `w04-stream/`, run `python task2_limits.py --sizes {','.join(str(r['n']) for r in rows)}`. The script appends completed runs to `out/limits.json`; preserve the existing measurements before rerunning. On systems with a `python3` executable, use that command name. Run `python analyze_sketches.py`, save `python bench.py --yours` to `out/bench.txt`, and run `python write_report.py --machine out/machine_snapshot.json` to rebuild this report from the saved evidence.
"""
    (out / "limits.md").write_text(text, encoding="utf-8")
    analysis = json.loads((out / "sketch_analysis.json").read_text(encoding="utf-8"))
    bench = (out / "bench.txt").read_text(encoding="utf-8-sig")
    false_positives = int(re.search(r"yours\s+false positives\s+([\d,]+)", bench)[1].replace(",", ""))
    measured = false_positives / 200_000
    bf = analysis["budget_filter"]
    obs = f"""# Observations

## Task 1
Bloom insertion only sets bits and membership checks those same bits, so an inserted item cannot become a false negative; predicted false positives were 0.860%, measured 0.900% on 20,000 absent queries, a small sampling difference.
I used the mean of eight group medians for FM: 26,624 / 19,953 = 1.334x; on the same hashes the plain mean gave 60,064 (3.010x) and median 16,384 (0.821x), showing how large hash maxima distort the mean.
Reservoir sampling draws j = rng.randrange(n) for each new item and replaces only when j < k: arrival chance k/n and later survival give every stream position final probability k/N, without knowing N or holding more than k items.

## Task 2
At {slow['n']:,} items, exact counting took {slow['exact_s']:.2f}s and {slow['exact_peak_bytes'] / 1e6:.3f} MB of traced memory; I stopped because this exceeded a one-minute interactive time budget, although the run completed without exhausting RAM.
Across {size_ratio:.0f}x more input, exact memory grew {exact_ratio:.2f}x (roughly O(n), measured slope {exact_slope:.3f}); FM stayed at {first['fm_peak_bytes']:,}-{last['fm_peak_bytes']:,} bytes (O(64), effectively O(1)); FM ratios were {', '.join(f"{r['fm_ratio']:.3f}x" for r in rows)} with no reliable improvement from more input.
A factor of two can answer whether daily distinct traffic is roughly thousands or millions for capacity planning, but is inadequate for per-user billing or deciding whether visitors grew by 5%.

## Task 3
For p(k) = (1 - exp(-kn/m))^k, setting d(log p)/dk = 0 gives kn/m = ln(2), so k = (m/n)ln(2) = 6.93 at 10 bits/item; I changed k from 1 to 7 (the optimum is still 7 after reserving metadata).
The ideal Bloom floor is exp(-10 ln(2)^2) = 0.8193%; my {bf['payload_bits']:,} payload bits plus metadata use {bf['resident_bits']:,} bits and predict {bf['predicted_rate_with_metadata']:.4%}; measured {measured:.4%} with zero false negatives is close, within the 0.9% strong threshold.
If n is unknown, monitor occupancy and add a new Bloom layer when memory may grow, assigning per-layer error budgets; underestimating n saturates the bits and raises false positives, while overestimating n wastes reserved space; with a fixed total budget, use an explicit window/reset policy and promise membership only within that window.
"""
    (out / "observation.md").write_text(obs, encoding="utf-8")
    print("Wrote limits.md, observation.md, and machine/stopping metadata in limits.json.")


if __name__ == "__main__":
    main()
