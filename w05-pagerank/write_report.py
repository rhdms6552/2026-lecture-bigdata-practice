"""Rebuild the written results from the measured JSON and benchmark output."""
import json
from pathlib import Path
import re


def main():
    out = Path(__file__).with_name('out')
    data = json.loads((out / 'convergence.json').read_text())
    snapshot = json.loads((out / 'machine_snapshot.json').read_text(encoding='utf-8-sig'))
    machine = data['machine']
    machine.update(cpu_model=snapshot['cpu'],
                   usable_ram_gib=snapshot['os']['TotalVisibleMemorySize'] / 2**20,
                   available_ram_gib=snapshot['os']['FreePhysicalMemory'] / 2**20,
                   captured_at=snapshot['captured_at'],
                   other_processes=sorted({p['ProcessName'] for p in snapshot['running']}))
    (out / 'convergence.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    rows = data['runs']
    assert all(r['converged'] and r['l1_change'] < r['tol'] for r in rows)
    betas = sorted((r for r in rows if r['nodes'] == 1200 and r['tol'] == 1e-10), key=lambda r: r['beta'])
    tolerances = sorted((r for r in rows if r['nodes'] == 1200 and r['beta'] == 0.85), key=lambda r: -r['tol'])
    sizes = sorted((r for r in rows if r['beta'] in (0.85, 0.95) and r['tol'] == 1e-10), key=lambda r: (r['beta'], r['nodes']))
    first_change = next(r for r in betas if r['top10'] != betas[0]['top10'])
    beta_table = '\n'.join(f"| {r['beta']} | {r['iterations']} | {r['seconds']:.6f} | {r['l1_change']:.3e} |" for r in betas)
    size_table = '\n'.join(f"| {r['beta']} | {r['nodes']:,} | {r['edges']:,} | {r['iterations']} | {r['seconds']:.6f} |" for r in sizes)
    tol_table = '\n'.join(f"| {r['tol']:.0e} | {r['iterations']} | {r['seconds']:.6f} | {r['l1_change']:.3e} |" for r in tolerances)
    ranking_table = '\n'.join(f"| {r['beta']} | {', '.join(r['top10'])} |" for r in betas)
    small = next(r for r in sizes if r['nodes'] == 1200 and r['beta'] == 0.85)
    big = next(r for r in sizes if r['nodes'] == 20000 and r['beta'] == 0.85)
    large = json.loads((out / 'large_graph.json').read_text())
    bench = (out / 'bench.txt').read_text(encoding='utf-8-sig')
    speed, memory = re.search(r'([\d.]+)x faster\s+([\d.]+)x less memory', bench).groups()
    worst = re.search(r'worst diff ([\deE+.-]+)', bench)[1]
    report = f"""# Task 2: convergence measurements

## Machine and method (A7)

- CPU: {machine['cpu_model']}; OS: {snapshot['os']['Caption']}; Python {machine['python']}.
- Usable RAM: {machine['usable_ram_gib']:.2f} GiB; available at snapshot: {machine['available_ram_gib']:.2f} GiB.
- Other running processes: {', '.join(machine['other_processes'])}. Snapshot: {machine['captured_at']}.
- Seed 246 and the unmodified `bench.build()` graph generator. Uniform starting ranks, uniform dangling redistribution, and uniform teleportation. Times measure PageRank only, excluding graph generation; they are single local runs and small differences are timing noise.
- The stopping rule is successive-iterate L1 change below tolerance, with a 5,000-iteration cap. All {len(rows)} runs actually converged; none hit the cap. JSON records the measured L1 change, rank sum, and top-10 scores as well as the required fields.

## Beta curve (A1-A3)

1,200 nodes, 5,877 edges, tolerance 1e-10:

| Beta | Iterations | Seconds | Final L1 change |
|---:|---:|---:|---:|
{beta_table}

Iterations rise from 14 to 24 as beta goes from 0.5 to 0.99. Increasing beta reduces teleportation and weakens the general contraction bound: differences can persist longer under link following. The increase is modest on this particular generated graph, rather than a dramatic blow-up near 1. Actual convergence also depends on graph structure and the starting vector; a worst-case bound based on beta alone can be loose. The slightly shorter time at 0.99 than 0.95 is measurement noise, despite one more iteration.

## Graph size (A4)

Before measuring, I predicted similar iteration counts but more wall time as the graph grew; `prediction.md` preserves that prediction.

| Beta | Nodes | Edges | Iterations | Seconds |
|---:|---:|---:|---:|---:|
{size_table}

The graph grew 16.67x in nodes and 17.30x in edges. At beta 0.85, iterations changed only from {small['iterations']} to {big['iterations']}, while time increased {big['seconds'] / small['seconds']:.2f}x. At beta 0.95 the counts similarly changed from 23 to 24. Each iteration performs O(n+E) work; the iteration count depends on mixing and tolerance rather than directly on n. The prediction was broadly right, although the counts were not exactly constant. These are different generated graphs, not a proof that graph size never affects convergence.

## Tolerance (A5)

1,200 nodes and beta 0.85:

| Tolerance | Iterations | Seconds | Final L1 change |
|---:|---:|---:|---:|
{tol_table}

Tightening 1e-3 to 1e-4 costs 2 iterations for one decimal digit; 1e-4 to 1e-6 costs 3 for two digits (1.5 per digit); 1e-6 to 1e-8 and 1e-8 to 1e-10 each cost 4 for two digits (2 per digit). Overall, seven additional digits cost 13 iterations, about 1.86 per digit. The tolerance range spans seven orders of magnitude and an absolute difference greater than 1e-4. These are digits of the L1 stopping threshold, not a guarantee of that many accurate digits in every rank.

## Top-10 sensitivity (A6)

| Beta | Ordered top 10 |
|---:|---|
{ranking_table}

The first **tested** order change is beta {first_change['beta']}: `p00004` overtakes `p00000`, moving from eighth to seventh. The exact crossing lies between tested beta 0.5 and 0.7 and was not located more precisely. The same ten pages remain in the set across all five betas; the first six positions are also unchanged. Thus membership is stable here, but the published order and scores still depend on the chosen beta. A published ranking should disclose beta and test sensitivity before treating small rank differences as robust.

## Reproduce

From `w05-pagerank/` (use `python3` instead of `python` where installed):

```text
python task2_convergence.py --betas 0.5,0.7,0.85,0.95,0.99
python task2_convergence.py --nodes 20000 --betas 0.85,0.95
python task2_convergence.py --tol 1e-3 --betas 0.85
python task2_convergence.py --tol 1e-4 --betas 0.85
python task2_convergence.py --tol 1e-6 --betas 0.85
python task2_convergence.py --tol 1e-8 --betas 0.85
```

The measurement script appends runs to `convergence.json`; preserve the original file before a fresh experiment. `write_report.py` builds the reports from those results, `machine_snapshot.json`, `large_graph.json`, and the saved `bench.py --yours` output in `bench.txt`.
"""
    (out / 'convergence.md').write_text(report, encoding='utf-8')
    observation = f"""# Observations

## Task 1
The broken version omits a dead end's rank from the next vector, so the sample graph drains to zero; I instead redistribute all dangling mass uniformly across every node, preserving total rank 1.
The update adds [(1-beta) + beta*dangling_mass]/n to each node: dangling redistribution replaces lost mass, while uniform teleportation lets the surfer leave a spider trap; the broken trap takes 100%, but the repaired graph keeps A=0.0375 and B=0.069375.
Beta is the probability of following an outgoing link; with probability 1-beta the surfer jumps to a uniformly chosen node, and at a dead end I also choose a uniformly random destination.

## Task 2
For 1,200 nodes and tol=1e-10, beta 0.5/0.7/0.85/0.95/0.99 required 14/17/20/23/24 iterations: less teleportation weakens contraction, although this graph's increase near 1 was modest; tightening tol from 1e-3 to 1e-10 added 13 iterations, about 1.86 per digit.
At beta=0.85, growing 1,200 to 20,000 nodes changed 20 to 21 iterations but {small['seconds']:.4f}s to {big['seconds']:.4f}s ({big['seconds']/small['seconds']:.1f}x); mixing controls the iteration count, while each pass must visit more nodes and edges.
The first tested top-10 order change was beta=0.7, where p00004 overtook p00000; membership stayed unchanged, so a published ranking should disclose beta and test whether close positions survive that choice.

## Task 3
I store integer adjacency lists and two rank vectors, using O(n+E) total space and a conservative 2n+12 float-slot bound: 2,412 versus 1,440,000 at n=1,200 ({memory}x fewer), with {speed}x measured speedup.
Teleportation and dangling redistribution contribute the same scalar to every node, so filling a length-n vector costs O(n); following only actual edges costs O(E), and neither requires an n-by-n matrix.
Worst per-node difference from dense was {worst}, caused by floating-point summation order and regrouping dangling contributions, well below 1e-9; the sparse version also solved 200,000 nodes in {large['solve_seconds']:.2f}s, where a dense float64 matrix alone would need 320 GB.
"""
    (out / 'observation.md').write_text(observation, encoding='utf-8')
    print('Wrote convergence.md and observation.md; added machine details to convergence.json.')


if __name__ == '__main__':
    main()
