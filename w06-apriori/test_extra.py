"""Verify exact counts, duplicate semantics, asymmetric rules, and collisions."""
from collections import Counter
from itertools import combinations
import random
import unittest

from task1_apriori import association_rules, frequent_pairs, frequent_singletons
from task3_pcy import YourAlgorithm


class ExtraChecks(unittest.TestCase):
    def test_asymmetric_confidence_and_lift(self):
        baskets = [{'a', 'b'}, {'a', 'b'}, {'a'}, {'c'}]
        rules = {(a, b): (c, lift) for a, b, c, lift in association_rules(baskets, 2, 0)}
        self.assertEqual(rules['a', 'b'], (2 / 3, 4 / 3))
        self.assertEqual(rules['b', 'a'], (1, 4 / 3))

    def test_duplicate_items_and_empty_input(self):
        baskets = [['a', 'a', 'b'], ['a', 'b', 'b'], []]
        self.assertEqual(frequent_singletons(baskets, 2), {'a': 2, 'b': 2})
        expected = {frozenset(('a', 'b')): 2}
        self.assertEqual(frequent_pairs(iter(baskets), 2), expected)
        self.assertEqual(YourAlgorithm(2, 8).run(baskets), expected)
        self.assertEqual(association_rules([], 1, 0), [])
        self.assertEqual(YourAlgorithm(1, 8).run([]), {})

    def test_random_data_and_bucket_collisions(self):
        for seed in range(12):
            rng = random.Random(seed)
            baskets = [set(rng.sample(range(18), rng.randrange(8))) for _ in range(60)]
            counts = Counter(frozenset(pair) for basket in baskets
                             for pair in combinations(basket, 2))
            for support in (1, 3, 8, 61):
                expected = {p: c for p, c in counts.items() if c >= support}
                self.assertEqual(frequent_pairs(baskets, support), expected)
                for buckets in (1, 8, 1024):
                    self.assertEqual(YourAlgorithm(support, buckets).run(baskets), expected)

    def test_saturation_and_larger_counter_type(self):
        for support in (255, 256, 300, 301):
            solver = YourAlgorithm(support, 8)
            got = solver.run([{'a', 'b'}] * 300)
            self.assertEqual(got, {frozenset(('a', 'b')): 300} if support <= 300 else {})
            self.assertEqual(solver.bucket_bytes, 8 if support <= 255 else 16)


if __name__ == '__main__':
    unittest.main()
