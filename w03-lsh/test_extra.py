"""Boundary checks beyond the supplied textbook/harness checks."""
import unittest

from task1_minhash import jaccard, lsh_candidates, minhash_signatures
from task2_crossover import build_documents
from task3_scale import YourFinder


class ExtraTests(unittest.TestCase):
    def test_hash_each_present_row_once(self):
        visited = []

        def h(row):
            visited.append(row)
            return 5 - row

        got = minhash_signatures([{0, 2}, {2, 4}, set()], [h], 5)
        self.assertEqual(visited, [0, 2, 4])
        self.assertEqual(got, [[3], [1], [float("inf")]])

    def test_banding_union_and_distinct_band_buckets(self):
        self.assertEqual(lsh_candidates([[1, 2], [1, 3], [4, 3], [2, 1]], 2),
                         {(0, 1), (1, 2)})
        self.assertEqual(lsh_candidates([[1, 2], [1, 2]], 2), {(0, 1)})
        self.assertEqual(lsh_candidates([], 2), set())

    def test_invalid_bands(self):
        for signatures, bands in [([[1, 2, 3]], 2), ([[1]], 0),
                                  ([[]], 1), ([[1], [1, 2]], 1)]:
            with self.assertRaises(ValueError):
                lsh_candidates(signatures, bands)

    def test_empty_and_identical_documents(self):
        docs = [set(), {1, 2}, {1, 2}, {3}]
        self.assertEqual(YourFinder(0.6).find(docs, jaccard), {(1, 2)})
        self.assertEqual(len(YourFinder(0).find(docs, jaccard)), 6)
        self.assertEqual(YourFinder(0.6).find([], jaccard), set())

    def test_generator_exceeds_original_cap(self):
        self.assertEqual(len(build_documents(4000)), 4000)
        self.assertEqual(build_documents(10), build_documents(10))


if __name__ == "__main__":
    unittest.main()
