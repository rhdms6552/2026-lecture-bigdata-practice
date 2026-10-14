"""Measure PCY's whole traced allocation peak, bucket size, and rule examples."""
import gc
import json
from pathlib import Path
import time
import tracemalloc

import bench
from task1_apriori import association_rules, frequent_singletons
from task3_pcy import PlainApriori, YourAlgorithm


def measured(cls, baskets, support=50, **kwargs):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    algo = cls(support, **kwargs)
    pairs = algo.run(baskets)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    row = dict(baskets=len(baskets), support=support, seconds=elapsed,
               peak_bytes=peak, pair_counters=algo.peak_counters, answers=len(pairs))
    if isinstance(algo, YourAlgorithm):
        row.update(buckets=algo.bucket_count, bucket_bytes=algo.bucket_bytes,
                   bitmap_bytes=algo.bitmap_bytes, frequent_buckets=algo.frequent_buckets)
    return row, pairs


def main():
    baskets = bench.build()
    singles = frequent_singletons(baskets, 50)
    rules = association_rules(baskets, 50, 0)
    a, b, confidence, lift = rules[0]
    reverse = next(r for r in rules if r[:2] == (b, a))
    result = {'rules': {'top': rules[0], 'reverse': reverse,
                       'antecedent_support': singles[a], 'consequent_support': singles[b],
                       'baskets': len(baskets), 'frequent_singletons': len(singles),
                       'all_possible_pairs': bench.ITEMS * (bench.ITEMS - 1) // 2,
                       'surviving_possible_pairs': len(singles) * (len(singles) - 1) // 2},
              'memory_comparison': [], 'bucket_comparison': []}
    out = Path(__file__).with_name('out')
    for n in (100, 500, 1000, 2000, 5000, 20000):
        subset = baskets[:n]
        plain, reference = measured(PlainApriori, subset)
        pcy, actual = measured(YourAlgorithm, subset)
        assert actual == reference, 'Compare support counts too, not only pair keys'
        result['memory_comparison'].append({'baskets': n, 'plain': plain, 'pcy': pcy})
        print(json.dumps(result['memory_comparison'][-1]), flush=True)
        del actual, reference
    result['bucket_comparison'].append(result['memory_comparison'][-1]['pcy'])
    reference = PlainApriori(50).run(baskets)
    for size in (1 << 16, 1 << 12):
        row, actual = measured(YourAlgorithm, baskets, bucket_count=size)
        assert actual == reference
        result['bucket_comparison'].append(row)
        print(json.dumps(row), flush=True)
        del actual
    (out / 'experiments.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
