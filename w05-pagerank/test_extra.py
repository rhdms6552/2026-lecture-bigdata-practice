"""Additional checks for stopping, edge cases, and dense equivalence."""
import random
import unittest

from task1_pagerank import pagerank, SIMPLE
from task3_sparse import DenseMatrix, YourPageRank


class PageRankChecks(unittest.TestCase):
    def test_empty_and_zero_iterations(self):
        self.assertEqual(pagerank({}), {})
        self.assertEqual(pagerank.iterations, 0)
        ranks = pagerank(SIMPLE, iterations=0)
        self.assertEqual(pagerank.iterations, 0)
        self.assertFalse(pagerank.converged)
        self.assertTrue(all(r == 1 / 3 for r in ranks.values()))

    def test_dangling_and_teleport_only(self):
        for graph, beta in [({'a': [], 'b': []}, 0.85), (SIMPLE, 0)]:
            ranks = pagerank(graph, beta=beta)
            self.assertEqual(pagerank.iterations, 1)
            self.assertTrue(all(abs(r - 1 / len(graph)) < 1e-15 for r in ranks.values()))
            self.assertEqual(YourPageRank(beta=beta).run(graph), ranks)

    def test_tolerance_and_iteration_cap(self):
        pagerank(SIMPLE, iterations=1, tol=1e-15)
        self.assertEqual(pagerank.iterations, 1)
        self.assertFalse(pagerank.converged)
        pagerank(SIMPLE, iterations=1000, tol=1e-12)
        self.assertLess(pagerank.iterations, 1000)
        self.assertLess(pagerank.delta, 1e-12)
        self.assertTrue(pagerank.converged)

    def test_random_graphs_against_dense(self):
        for seed in range(10):
            rng = random.Random(seed)
            nodes = list(range(17))
            graph = {v: rng.sample(nodes, rng.randrange(7)) for v in nodes}
            for beta in (0.5, 0.85, 0.99):
                dense = DenseMatrix(beta=beta, max_iter=1000, tol=1e-12).run(graph)
                sparse = YourPageRank(beta=beta, max_iter=1000, tol=1e-12)
                for ranks in (pagerank(graph, beta, 1000, 1e-12), sparse.run(graph)):
                    self.assertAlmostEqual(sum(ranks.values()), 1, places=11)
                    self.assertLess(max(abs(ranks[v] - dense[v]) for v in nodes), 1e-9)
                self.assertEqual(sparse.memory_floats(), 2 * len(nodes) + 12)
        self.assertEqual(sparse.run({}), {})
        self.assertEqual(sparse.iterations, 0)


if __name__ == '__main__':
    unittest.main()
