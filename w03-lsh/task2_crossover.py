#!/usr/bin/env python3
"""Week 3 · Task 2 — Find the crossover on your own machine.

Textbook §3.4.

Everybody knows brute force is quadratic and LSH is not. That is not the
interesting question. The interesting question is **where, on the machine in
front of you, does it start to matter** - and that answer is yours alone. It
depends on your CPU, your memory, and how big your shingle sets are.

This script gives you the timing loop. The two methods are yours: import them
from Task 1 and Task 3.

    python3 task2_crossover.py --sizes 500,1000,2000,4000
    python3 task2_crossover.py --sizes 8000,16000          # keep going

Write down where it hurts. That is the deliverable.
"""
import argparse, json, os, platform, random, subprocess, time, tracemalloc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
    }
    if platform.system() == "Windows":
        command = ("$cpu = (Get-CimInstance Win32_Processor).Name; "
                   "$ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory; "
                   "@{cpu=$cpu; ram_bytes=$ram} | ConvertTo-Json -Compress")
        info.update(json.loads(subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command], text=True)))
    info["background_apps"] = "Codex, Chrome and Edge were open; no other benchmark was run concurrently."
    return info


def build_documents(n, seed=246):
    """Generate exactly n documents; bench.build() is capped at 2,120.

    Keep the harness's 60 shingles / 5,000 vocabulary and roughly 120/2,120
    near-duplicate fraction. Leave bench.py itself unchanged.
    """
    import bench
    if n < 1:
        raise ValueError("document count must be positive")
    rng = random.Random(seed)
    planted = n * bench.PLANTED // (bench.N_DOCS + bench.PLANTED)
    base_n = n - planted
    docs = [set(rng.sample(range(bench.VOCAB), bench.SHINGLES))
            for _ in range(base_n)]
    for _ in range(planted):
        clone = set(docs[rng.randrange(base_n)])
        for _ in range(rng.randint(4, 14)):
            clone.discard(rng.choice(list(clone)))
            clone.add(rng.randrange(bench.VOCAB))
        docs.append(clone)
    rng.shuffle(docs)
    assert len(docs) == n
    return docs


def timed(fn, *args):
    """Wall time and peak memory of one call."""
    tracemalloc.start()
    t0 = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="250,500,1000,2000",
                   help="comma-separated document counts to try")
    p.add_argument("--threshold", type=float, default=0.6)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    import bench
    from task3_scale import BruteForce
    try:
        from task3_scale import YourFinder
    except Exception:
        YourFinder = None

    path = os.path.join(OUT, "crossover.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            prior = json.load(f)
    else:
        prior = {"runs": []}
    prior["machine"] = machine()
    prior["method"] = {"seed": 246, "shingles": bench.SHINGLES,
                       "vocabulary": bench.VOCAB, "num_hashes": 120, "bands": 30,
                       "memory": "tracemalloc peak during find; input generation excluded"}
    for n in [int(x) for x in a.sizes.split(",")]:
        docs = build_documents(n)
        print(f"  starting n={n:,} ({len(docs):,} actual documents)", flush=True)
        sim = bench.Counter()
        _, t_brute, m_brute = timed(BruteForce(a.threshold).find, docs, sim)
        c_brute = sim.calls

        assert c_brute == n * (n - 1) // 2
        row = {"n": n, "actual_docs": len(docs), "threshold": a.threshold,
               "brute_s": t_brute, "brute_calls": c_brute,
               "brute_peak_bytes": m_brute}

        if YourFinder is not None:
            sim2 = bench.Counter()
            try:
                _, t_lsh, m_lsh = timed(YourFinder(a.threshold).find, docs, sim2)
                row.update({"lsh_s": t_lsh, "lsh_calls": sim2.calls,
                            "lsh_peak_bytes": m_lsh})
            except NotImplementedError:
                pass

        prior["runs"].append(row)
        # Save each completed size so an interrupted larger run loses nothing.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prior, f, indent=2)
        line = f"  n={n:>6}  brute {t_brute:>8.2f}s  {c_brute:>12,} cmp"
        if "lsh_s" in row:
            line += f"   |  lsh {row['lsh_s']:>7.2f}s  {row['lsh_calls']:>9,} cmp"
        print(line, flush=True)

    print(f"\n  -> out/crossover.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until something becomes unpleasant. Record where.")


if __name__ == "__main__":
    main()
