"""Write the tables, plot, and three-line observations from measured evidence."""
import json
from pathlib import Path


def main():
    out = Path(__file__).with_name('out')
    data = json.loads((out / 'explosion.json').read_text())
    experiments = json.loads((out / 'experiments.json').read_text())
    stress = json.loads((out / 'stress_limit.json').read_text())
    snapshot = json.loads((out / 'machine_snapshot.json').read_text(encoding='utf-8-sig'))
    data['machine'].update(cpu_model=snapshot['cpu'],
        usable_ram_gib=snapshot['os']['TotalVisibleMemorySize'] / 2**20,
        available_ram_gib=snapshot['os']['FreePhysicalMemory'] / 2**20,
        captured_at=snapshot['captured_at'],
        other_processes=sorted({r['ProcessName'] for r in snapshot['running']}))
    data['stress_probe'] = stress
    (out / 'explosion.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    rows = sorted(data['runs'], key=lambda r: -r['support'])
    by_support = {r['support']: r for r in rows}
    stopped = stress['runs'][-1]
    assert not stopped['completed'], 'Continue the stress experiment or report no limit honestly.'
    reason = '512 MiB traced-memory budget' if stopped['stop_reason'] == 'memory_budget' else '60-second counting-time budget'
    baseline = by_support[50]
    small = by_support[1]
    rules = experiments['rules']
    a, b, confidence, lift = rules['top']
    reverse = rules['reverse'][2]
    memory_rows = experiments['memory_comparison']
    full = memory_rows[-1]
    buckets = sorted(experiments['bucket_comparison'], key=lambda r: -r['buckets'])
    machine = data['machine']
    growth = [rows[i]['peak_counters'] / rows[i-1]['peak_counters'] for i in range(1, len(rows))]
    table = '\n'.join(f"| {r['support']} | {r['peak_counters']:,} | {r['frequent_pairs']:,} | {r['peak_counters']/r['frequent_pairs']:.2f} | {r['seconds']:.2f} | {r['peak_bytes']/1e6:.2f} |" for r in rows)
    stress_table = '\n'.join(f"| {r['support']} | {r['processed_baskets']:,} | {r['candidate_counters']:,} | {r['seconds']:.2f} | {r['peak_bytes']/1e6:.2f} | {r['stop_reason'] or 'completed'} |" for r in stress['runs'])
    memory_table = '\n'.join(f"| {r['baskets']:,} | {r['plain']['peak_bytes']/1e6:.3f} | {r['pcy']['peak_bytes']/1e6:.3f} | {r['plain']['pair_counters']:,} | {r['pcy']['pair_counters']:,} |" for r in memory_rows)
    bucket_table = '\n'.join(f"| {r['buckets']:,} | {r['frequent_buckets']:,} | {r['bucket_bytes']:,} | {r['bitmap_bytes']:,} | {r['pair_counters']:,} | {r['peak_bytes']/1e6:.3f} |" for r in buckets)
    report = f"""# Task 2: support, candidate counters, and practical limits

## Machine and measurement (A6)

- CPU: {machine['cpu_model']}; {snapshot['os']['Caption']}; Python {machine['python']}.
- Usable RAM {machine['usable_ram_gib']:.2f} GiB; available at snapshot {machine['available_ram_gib']:.2f} GiB.
- Other running processes: {', '.join(machine['other_processes'])}; snapshot {machine['captured_at']}.
- Main sweep: the original 20,000 baskets, 2,000 items, seed 246 from unmodified `bench.build()`. Every support uses the same baskets and the unchanged `PlainApriori` baseline.
- Peak bytes are allocations traced during the algorithm, including pair counting and construction of its answer dictionary, but excluding the already-built input baskets, interpreter, and tracemalloc's own bookkeeping. They are not process RSS. Tracing slows these runs relative to `bench.txt`.
- Each completed row is saved immediately. The prior answer dictionary is released before the next threshold, so previous answers are not intentionally kept alive.

## Main sweep (A1, A3, A5)

| Support | Peak pair counters | Frequent pairs | Counters / answer | Seconds | Traced peak MB |
|---:|---:|---:|---:|---:|---:|
{table}

![Counters and answers as support falls](explosion.png)

## Actual growth (A4, A5)

For support 400 -> 200 -> 100 -> 50, counters multiply by {growth[0]:.2f}x, {growth[1]:.2f}x, and {growth[2]:.2f}x: substantially worse than doubling per halving. At support 50, {baseline['peak_counters']:,} counters produce only {baseline['frequent_pairs']:,} answers, a {baseline['peak_counters']/baseline['frequent_pairs']:.1f}:1 ratio. Singleton filtering lets many candidate pairs through even though their joint counts are below support.

The growth does **not** continue indefinitely on this fixed dataset. From support 25 down to 1, counters plateau at 893,456, because every observed pair is already a candidate; lowering support cannot create new co-occurrences. Answers instead rise from 17,045 to 893,456 as more stored counts cross the threshold. At support 1 every observed candidate is an answer. Thus the measured curve initially has rapidly growing candidate overhead, then a plateau in counters with continued answer growth; it is not honest to claim exponential growth at every threshold.

The small non-monotonic change in peak bytes around support 50/25 reflects allocation and dictionary resizing effects, not fewer candidate pairs. At very low support, constructing the much larger returned answer dictionary increases the peak further.

## Where I stopped (A2)

The supplied dataset still completed at support 1: {small['seconds']:.2f}s and {small['peak_bytes']/1e6:.2f} MB of traced allocations. This did not exhaust this machine, and there is no meaningful lower positive integer support. I therefore enlarged the experiment to **10,000 items and 80,000 baskets**, retaining seed 246 and the same generator.

Before that probe, I set practical limits of **512 MiB traced allocations or 60 seconds per counting run**, checked every 128 baskets. The input is outside tracing and tracemalloc has additional overhead, so these limits leave room for the browser and other applications; they are experiment budgets, not a claim of the machine's physical RAM ceiling.

| Support | Pass-two baskets processed | Candidate counters | Seconds | Traced peak MB | Status |
|---:|---:|---:|---:|---:|---|
{stress_table}

The first stopped run was support **{stopped['support']}**, at {stopped['seconds']:.2f}s and {stopped['peak_bytes']/1e6:.2f} MB, after {stopped['processed_baskets']:,}/{stopped['baskets']:,} baskets in pass two: it crossed the **{reason}**. The limit is checked periodically, not enforced by the allocator; a dictionary resize can temporarily exceed it before the next check, which explains why the recorded peak is above the trigger. This is an intentional early stop, not an OS out-of-memory error. Its counters are a partial-run measurement, and its final frequent-pair count is explicitly null. The larger probe uses the same Apriori counting steps but checks the budget and does not materialize a result dictionary; its peaks should not be confused with the main sweep's complete-answer peaks.

## Reproduce

Run `python task2_explosion.py --supports 400,200,100,50,25,12,6,3,1`, then `python stress_limit.py`. The first appends to `explosion.json`; preserve the old measurement file for a fresh run. Run `python experiments.py` for rule examples, PCY byte peaks, and bucket-size comparisons, then `python write_report.py` for the reports and plot. Use `python3` where that is the Python 3 command. Plotting requires matplotlib; the required algorithms and lab checks use only the standard library.
"""
    (out / 'explosion.md').write_text(report, encoding='utf-8')
    notes = f"""# PCY memory accounting and rule evidence

## Rules and candidate counts

At support 50 on the generated dataset, the highest-confidence rule (ties sorted by item ID) was **{a} -> {b}**, confidence {confidence:.6f}, lift {lift:.6f}; reverse confidence {reverse:.6f}. Antecedent support was {rules['antecedent_support']}, consequent support {rules['consequent_support']}, out of {rules['baskets']:,} baskets. Its lift compares the prediction to the consequent's baseline frequency, so high confidence alone is not sufficient evidence of a useful relationship. These are associations in generated data, not causal claims or validated retail recommendations.

All pairs among 2,000 items would require {rules['all_possible_pairs']:,} counters. Pass one leaves {rules['frequent_singletons']:,} frequent singletons, hence {rules['surviving_possible_pairs']:,} possible survivor pairs. The sparse baseline actually allocates counters only for {baseline['peak_counters']:,} observed survivor pairs. These are three different counts.

## Bucket memory is included

PCY uses 1,048,576 buckets. During pass one, counts saturate at support: values beyond 50 cannot change whether a bucket is frequent. `array('B')` therefore stores each bucket in one byte at support 50, for **1,048,576 payload bytes (1 MiB)**. Larger supports select wider integer types. Saturation cannot hide a frequent pair: its bucket total is at least its own count, so it always reaches the threshold.

The bitmap is packed into **131,072 bytes (128 KiB)**. Bucket counts and bitmap coexist briefly during conversion (1,179,648 payload bytes); the counts array is then deleted before pair counters are allocated. Singleton counts, ID mapping, sets, dictionary keys, output, and allocation overhead are all included in the separately measured tracemalloc peak below. The harness's `peak_counters` counts pair-specific counting entries, not bucket slots or physical bytes; a 98.4% counter reduction alone would not prove the same percentage of byte savings.

At 20,000 baskets, total traced allocation peaks were **{full['plain']['peak_bytes']/1e6:.3f} MB for plain Apriori** versus **{full['pcy']['peak_bytes']/1e6:.3f} MB for PCY**, a {full['plain']['peak_bytes']/full['pcy']['peak_bytes']:.2f}x ratio. PCY is slower in the untraced benchmark because it hashes pairs in both passes. This task scores memory, not speed.

## Crossover with a fixed support of 50

All prefixes come from the same generated 20,000-basket dataset; comparisons verify the entire answer dictionary, including support counts.

| Baskets | Plain peak MB | PCY peak MB | Plain pair counters | PCY pair counters |
|---:|---:|---:|---:|---:|
{memory_table}

The sampled byte-memory crossover lies **between 2,000 and 5,000 baskets**: plain is smaller at 2,000, PCY smaller at 5,000. This range is specific to support 50, this distribution, the 2,000-item universe, and the chosen bucket count. Fewer buckets reduce fixed array cost but increase collisions; more distinct items, larger baskets, support, and skew all change the crossover.

## Smaller bucket arrays

20,000 baskets, support 50; all variants return exactly the same pairs and counts.

| Buckets | Frequent buckets | Bucket bytes | Bitmap bytes | Pair counters | Whole traced peak MB |
|---:|---:|---:|---:|---:|---:|
{bucket_table}

A small array combines many unrelated pairs into each bucket. Those buckets become frequent even if most individual pairs are not, so the bitmap admits more candidates and the pass-two dictionary grows. The 1,048,576-bucket choice is a measured tradeoff that filters well here, not a universally optimal size.
"""
    (out / 'memory_accounting.md').write_text(notes, encoding='utf-8')
    obs = f"""# Observations

## Task 1
On the generated data at support 50, {a}->{b} had confidence {confidence:.4f}, whereas {b}->{a} had {reverse:.4f}; the first direction is the more reliable conditional prediction, because the antecedent supports differ.
The highest-confidence rule was {a}->{b}, with lift {lift:.4f}; it improves on {b}'s baseline frequency on these baskets, but I would not treat a generated-data association as a causal or validated shopping recommendation.
Brute force over 2,000 items needs {rules['all_possible_pairs']:,} pair counters; pass one retains {rules['frequent_singletons']:,} items ({rules['surviving_possible_pairs']:,} possible pairs), and Apriori allocates {baseline['peak_counters']:,} observed-pair counters after pruning.

## Task 2
The default data still fit at support 1 ({small['peak_bytes']/1e6:.1f} MB); with 10,000 items/80,000 baskets I stopped at support {stopped['support']} after {stopped['seconds']:.2f}s and {stopped['peak_bytes']/1e6:.1f} MB because the {reason} was reached, not because the OS ran out of memory.
For support 400->200->100->50, counters grew {growth[0]:.2f}x/{growth[1]:.2f}x/{growth[2]:.2f}x per halving; from 25 to 1 they plateaued at 893,456, since all observed pairs were already candidates.
At support 50, 820,259 counters found only 6,397 answers (128.2 counters/answer); below 25 the counters stayed fixed while answers grew from 17,045 to 893,456, so a lower threshold can inflate candidate overhead first and output size later.

## Task 3
I chose 1,048,576 buckets; threshold-saturated byte counters cost 1 MiB, and the packed bitmap costs 128 KiB (both coexist briefly); deleting the counters before pass two reduced pair counters from 820,259 to 13,109, with exactly the same pairs and supports.
Including metadata and outputs, traced peaks were {full['plain']['peak_bytes']/1e6:.2f} MB plain versus {full['pcy']['peak_bytes']/1e6:.2f} MB PCY; the sampled memory crossover was between 2,000 and 5,000 baskets at support 50, and depends on support, item distribution, and bucket count.
Shrinking to {buckets[-1]['buckets']:,} buckets raised pair counters to {buckets[-1]['pair_counters']:,} and traced peak to {buckets[-1]['peak_bytes']/1e6:.2f} MB: collisions made the bitmap admit too many pairs; reducing the bucket array alone did not reduce total memory.
"""
    (out / 'observation.md').write_text(obs, encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5.2), constrained_layout=True)
    supports = [r['support'] for r in rows]
    ax.plot(supports, [r['peak_counters'] for r in rows], 'o-', color='#2457A7', label='Peak candidate-pair counters', linewidth=2)
    ax.plot(supports, [r['frequent_pairs'] for r in rows], 's-', color='#D47814', label='Frequent pairs returned', linewidth=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.invert_xaxis()
    ax.set_xticks(supports, [str(s) for s in supports])
    ax.set_xlabel('Support threshold (lower to the right)')
    ax.set_ylabel('Count (log scale)')
    ax.set_title('Apriori: candidate overhead grows, then counters plateau\n20,000 baskets, 2,000 items, seed 246')
    ax.grid(True, which='major', alpha=0.2)
    ax.legend(loc='upper left')
    fig.savefig(out / 'explosion.png', dpi=180)
    fig.savefig(out / 'explosion.svg')
    plt.close(fig)
    print('Wrote explosion.md, memory_accounting.md, observation.md, and both plot formats.')


if __name__ == '__main__':
    main()
