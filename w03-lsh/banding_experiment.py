"""Measure the cost of moving the S-curve above the similarity threshold."""
import json
from pathlib import Path

import bench
from task1_minhash import lsh_candidates
from task3_scale import YourFinder


def main():
    docs = bench.build()
    truth = bench.truth(docs)
    signatures = YourFinder(bench.THRESHOLD).signatures(docs)
    results = []
    for bands in (30, 15, 10):
        rows = 120 // bands
        candidates = lsh_candidates(signatures, bands)
        counter = bench.Counter()
        found = {(i, j) for i, j in candidates
                 if counter(docs[i], docs[j]) >= bench.THRESHOLD}
        result = dict(hashes=120, bands=bands, rows=rows,
                      step=(1 / bands) ** (1 / rows),
                      probability_at_threshold=1 - (1 - bench.THRESHOLD ** rows) ** bands,
                      candidates=counter.calls, true_pairs=len(truth),
                      hits=len(found & truth), recall=len(found & truth) / len(truth),
                      precision=len(found & truth) / len(found) if found else 1.0)
        results.append(result)
        print(json.dumps(result), flush=True)
    path = Path(__file__).parent / "out" / "banding.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
