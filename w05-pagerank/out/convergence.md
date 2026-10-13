# Task 2: convergence measurements

## Machine and method (A7)

- CPU: 12th Gen Intel(R) Core(TM) i7-1260P; OS: Microsoft Windows 11 Home; Python 3.11.8.
- Usable RAM: 15.63 GiB; available at snapshot: 3.79 GiB.
- Other running processes: ChatGPT, Memory Compression, MsMpEng, asdsvc, chrome, explorer. Snapshot: 2026-10-13T19:08:59.3100062+09:00.
- Seed 246 and the unmodified `bench.build()` graph generator. Uniform starting ranks, uniform dangling redistribution, and uniform teleportation. Times measure PageRank only, excluding graph generation; they are single local runs and small differences are timing noise.
- The stopping rule is successive-iterate L1 change below tolerance, with a 5,000-iteration cap. All 11 runs actually converged; none hit the cap. JSON records the measured L1 change, rank sum, and top-10 scores as well as the required fields.

## Beta curve (A1-A3)

1,200 nodes, 5,877 edges, tolerance 1e-10:

| Beta | Iterations | Seconds | Final L1 change |
|---:|---:|---:|---:|
| 0.5 | 14 | 0.008571 | 2.278e-11 |
| 0.7 | 17 | 0.012103 | 5.324e-11 |
| 0.85 | 20 | 0.013512 | 7.369e-11 |
| 0.95 | 23 | 0.014839 | 4.742e-11 |
| 0.99 | 24 | 0.014385 | 5.235e-11 |

Iterations rise from 14 to 24 as beta goes from 0.5 to 0.99. Increasing beta reduces teleportation and weakens the general contraction bound: differences can persist longer under link following. The increase is modest on this particular generated graph, rather than a dramatic blow-up near 1. Actual convergence also depends on graph structure and the starting vector; a worst-case bound based on beta alone can be loose. The slightly shorter time at 0.99 than 0.95 is measurement noise, despite one more iteration.

## Graph size (A4)

Before measuring, I predicted similar iteration counts but more wall time as the graph grew; `prediction.md` preserves that prediction.

| Beta | Nodes | Edges | Iterations | Seconds |
|---:|---:|---:|---:|---:|
| 0.85 | 1,200 | 5,877 | 20 | 0.013512 |
| 0.85 | 20,000 | 101,665 | 21 | 0.249879 |
| 0.95 | 1,200 | 5,877 | 23 | 0.014839 |
| 0.95 | 20,000 | 101,665 | 24 | 0.260469 |

The graph grew 16.67x in nodes and 17.30x in edges. At beta 0.85, iterations changed only from 20 to 21, while time increased 18.49x. At beta 0.95 the counts similarly changed from 23 to 24. Each iteration performs O(n+E) work; the iteration count depends on mixing and tolerance rather than directly on n. The prediction was broadly right, although the counts were not exactly constant. These are different generated graphs, not a proof that graph size never affects convergence.

## Tolerance (A5)

1,200 nodes and beta 0.85:

| Tolerance | Iterations | Seconds | Final L1 change |
|---:|---:|---:|---:|
| 1e-03 | 7 | 0.004447 | 5.197e-04 |
| 1e-04 | 9 | 0.005882 | 3.025e-05 |
| 1e-06 | 12 | 0.006174 | 4.536e-07 |
| 1e-08 | 16 | 0.008439 | 4.165e-09 |
| 1e-10 | 20 | 0.013512 | 7.369e-11 |

Tightening 1e-3 to 1e-4 costs 2 iterations for one decimal digit; 1e-4 to 1e-6 costs 3 for two digits (1.5 per digit); 1e-6 to 1e-8 and 1e-8 to 1e-10 each cost 4 for two digits (2 per digit). Overall, seven additional digits cost 13 iterations, about 1.86 per digit. The tolerance range spans seven orders of magnitude and an absolute difference greater than 1e-4. These are digits of the L1 stopping threshold, not a guarantee of that many accurate digits in every rank.

## Top-10 sensitivity (A6)

| Beta | Ordered top 10 |
|---:|---|
| 0.5 | p00009, p00001, p00006, p00005, p00003, p00002, p00000, p00004, p00007, p00008 |
| 0.7 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.85 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.95 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.99 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |

The first **tested** order change is beta 0.7: `p00004` overtakes `p00000`, moving from eighth to seventh. The exact crossing lies between tested beta 0.5 and 0.7 and was not located more precisely. The same ten pages remain in the set across all five betas; the first six positions are also unchanged. Thus membership is stable here, but the published order and scores still depend on the chosen beta. A published ranking should disclose beta and test sensitivity before treating small rank differences as robust.

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
