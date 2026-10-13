"""Run the sparse solver at a size whose dense matrix exceeds this PC's RAM."""
import json
from pathlib import Path
import time

import bench
from task3_sparse import YourPageRank


def main():
    bench.NODES = 200_000
    start = time.perf_counter()
    graph = bench.build()
    build_seconds = time.perf_counter() - start
    solver = YourPageRank(max_iter=1000)
    start = time.perf_counter()
    ranks = solver.run(graph)
    elapsed = time.perf_counter() - start
    n = len(graph)
    # Independently check one more PageRank update against the returned vector.
    base = ((1 - solver.beta) + solver.beta * sum(ranks[v] for v in graph if not graph[v])) / n
    next_ranks = dict.fromkeys(graph, base)
    for v, outs in graph.items():
        if outs:
            share = solver.beta * ranks[v] / len(outs)
            for w in outs:
                next_ranks[w] += share
    residual = sum(abs(next_ranks[v] - ranks[v]) for v in graph)
    assert abs(sum(ranks.values()) - 1) < 1e-8
    assert residual < solver.tol
    result = {
        "nodes": n, "edges": sum(map(len, graph.values())),
        "build_seconds": build_seconds, "solve_seconds": elapsed,
        "iterations": solver.iterations, "rank_sum": sum(ranks.values()),
        "fixed_point_l1_residual": residual, "float_slots_bound": solver.memory_floats(),
        "dense_float_slots": n * n, "dense_float64_bytes": n * n * 8,
        "note": "Dense size is calculated, not allocated; float-slot counts are not process RSS. Residual validation uses additional memory after the timed solver run.",
    }
    out = Path(__file__).with_name('out')
    out.mkdir(exist_ok=True)
    (out / 'large_graph.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
