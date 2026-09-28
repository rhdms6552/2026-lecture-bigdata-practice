"""Check streaming and actual retained-memory properties beyond the harness."""
import hashlib
import struct
import sys
import unittest

from task1_sketches import BloomFilter, flajolet_martin, fm_registers, reservoir_sample
from task3_budget import YourFilter


class OnePass:
    def __init__(self, values):
        self.values = values
        self.started = False

    def __iter__(self):
        if self.started:
            raise AssertionError("stream was scanned twice")
        self.started = True
        yield from self.values


class StreamTests(unittest.TestCase):
    def test_optimized_registers_equal_simple_loop(self):
        for seed in (0, 246):
            for count in (1, 9, 64):
                maxima = [0] * count
                key = hashlib.sha256(str(seed).encode()).digest()
                for item in range(2000):
                    digest = hashlib.shake_256(key + str(item).encode()).digest(8 * count)
                    for i, value in enumerate(struct.unpack("<" + "Q" * count, digest)):
                        zeros = (value & -value).bit_length() - 1 if value else 64
                        maxima[i] = max(maxima[i], zeros)
                self.assertEqual(fm_registers(OnePass(range(2000)), count, seed)[0], maxima)

    def test_bloom_insertions_and_packed_storage(self):
        bf = BloomFilter(103, 4)
        self.assertEqual(len(bf.bits), 13)
        self.assertEqual(bf.expected_fp_rate(0), 0)
        for i in range(1000):
            bf.add(i)
        self.assertTrue(all(i in bf for i in range(1000)))

    def test_fm_empty_and_duplicates(self):
        self.assertEqual(flajolet_martin(OnePass([])), 0)
        a = flajolet_martin(OnePass(range(1000)))
        b = flajolet_martin(OnePass(i % 1000 for i in range(5000)))
        self.assertEqual(a, b)

    def test_reservoir_short_zero_and_one_pass(self):
        self.assertEqual(reservoir_sample(OnePass(range(3)), 5), [0, 1, 2])
        self.assertEqual(reservoir_sample(OnePass(range(10)), 0), [])
        sample = reservoir_sample(OnePass(range(10000)), 10)
        self.assertEqual(len(sample), 10)
        self.assertEqual(len(set(sample)), 10)

    def test_real_filter_state_fits(self):
        for budget in (8000, 80000, 80003):
            f = YourFilter(budget)
            actual = 8 * (sys.getsizeof(f) + sys.getsizeof(f._state))
            self.assertEqual(f.memory_bits(), actual)
            self.assertLessEqual(actual, budget)
            self.assertFalse(hasattr(f, "__dict__"))
            for i in range(1000):
                f.add(i)
            self.assertTrue(all(i in f for i in range(1000)))
            self.assertEqual(f.memory_bits(), actual)

    def test_invalid_configuration(self):
        for m, k in ((0, 1), (8, 0)):
            with self.assertRaises(ValueError):
                BloomFilter(m, k)
        with self.assertRaises(ValueError):
            flajolet_martin([], n_hashes=0)
        with self.assertRaises(ValueError):
            reservoir_sample([], -1)
        with self.assertRaises(ValueError):
            YourFilter(8)


if __name__ == "__main__":
    unittest.main()
