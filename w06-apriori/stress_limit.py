"""Bounded larger-data probe when the provided 2,000-item dataset still fits.

Stop at 512 MiB of traced allocations or 60 seconds of counting, whichever
comes first. These are practical experiment limits, not a claimed OS OOM.
"""
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import time
import tracemalloc

import bench


def measure(baskets, support, memory_limit=512 * 2**20, seconds_limit=60):
    tracemalloc.start()
    start = time.perf_counter()
    singles = Counter()
    for basket in baskets:
        singles.update(basket)
    frequent = {item for item, count in singles.items() if count >= support}
    counts = Counter()
    reason = None
    for processed, basket in enumerate(baskets, 1):
        for pair in combinations(sorted(basket & frequent), 2):
            counts[pair] += 1
        if processed % 128 == 0:
            _, peak = tracemalloc.get_traced_memory()
            if peak >= memory_limit:
                reason = 'memory_budget'
            elif time.perf_counter() - start >= seconds_limit:
                reason = 'time_budget'
            if reason:
                break
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return dict(support=support, items=bench.ITEMS, baskets=len(baskets),
                processed_baskets=processed, frequent_singletons=len(frequent),
                candidate_counters=len(counts), seconds=elapsed, peak_bytes=peak,
                completed=reason is None, stop_reason=reason,
                frequent_pairs=sum(c >= support for c in counts.values()) if reason is None else None,
                memory_limit_bytes=memory_limit, seconds_limit=seconds_limit)


def main():
    bench.ITEMS, bench.BASKETS = 10_000, 80_000
    start = time.perf_counter()
    baskets = bench.build()
    result = {'build_seconds': time.perf_counter() - start,
              'method': 'Same seed and unmodified bench.build with a larger item universe and basket count. Exact Apriori pair counting with a budget check every 128 baskets; input baskets are built before tracing. Incomplete runs have no final frequent-pair answer.',
              'runs': []}
    out = Path(__file__).with_name('out')
    for support in (200, 100, 50, 25, 12, 6, 3, 1):
        row = measure(baskets, support)
        result['runs'].append(row)
        (out / 'stress_limit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(row), flush=True)
        if not row['completed']:
            break


if __name__ == '__main__':
    main()
