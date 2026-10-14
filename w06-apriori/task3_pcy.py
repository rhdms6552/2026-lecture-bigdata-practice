#!/usr/bin/env python3
"""Week 6 · Task 3 — Make pass two fit.

Textbook §6.3 (PCY), §6.3.2 - §6.3.4.

`PlainApriori` does what Task 1 asked: use pass one to drop infrequent items,
then count every pair of surviving items. That is already much better than
counting all pairs. It is still not enough, because the surviving items are the
common ones, and the common ones appear together constantly.

The harness measures **the peak number of pair counters you held**, because
that is the thing that decides whether the algorithm runs at all. §6.3 is about
spending pass one's spare memory to shrink it.

    python3 bench.py
    python3 bench.py --yours

Correctness first: you must find exactly the same frequent pairs. Finding fewer
is not an optimisation.
"""
from collections import Counter
from itertools import combinations
from array import array


class PlainApriori:
    """Pass one drops infrequent items. Pass two counts every surviving pair."""

    def __init__(self, support):
        self.support = support
        self.peak_counters = 0

    def run(self, baskets):
        counts = Counter()
        for basket in baskets:
            counts.update(basket)
        frequent = {i for i, c in counts.items() if c >= self.support}

        pair_counts = Counter()
        for basket in baskets:
            items = sorted(basket & frequent)
            for pair in combinations(items, 2):
                pair_counts[pair] += 1
            self.peak_counters = max(self.peak_counters, len(pair_counts))

        return {frozenset(p): c for p, c in pair_counts.items()
                if c >= self.support}


class YourAlgorithm:
    """Your frequent-pair finder.

        __init__(support)
        run(baskets) -> {frozenset({a, b}): count}
        .peak_counters -> the most pair counters you ever held at once

    Same pairs as the baseline. Fewer counters.

    Pass one only needs one integer per item, and there are not many items. The
    rest of your memory is sitting idle while you do it. §6.3 spends it: hash
    every pair you see in pass one into a fixed array of buckets, and count the
    buckets rather than the pairs.

    A bucket whose total is below the support threshold cannot contain a
    frequent pair. In pass two you skip every pair landing in such a bucket -
    and the bucket array collapses to a bitmap, one bit each, before you need
    the memory for counters.

    Two things to be careful of:

      * a bucket being frequent does not make its pairs frequent. It is a
        filter, not an answer
      * `peak_counters` is on your honour. Count the pair counters you hold at
        the same time. The bitmap is not a pair counter, but if you keep the
        full bucket counts alive into pass two, that is not free either -
        observation.md asks about it
    """

    def __init__(self, support, bucket_count=1 << 20):
        if support <= 0 or support >= 2 ** 64 or bucket_count <= 0:
            raise ValueError("invalid support or bucket count")
        self.support = support
        self.bucket_count = bucket_count
        self.peak_counters = 0

    @staticmethod
    def _bucket(a, b, count):
        if a > b:
            a, b = b, a
        return ((a * 0x9E3779B1) ^ (b * 0x85EBCA6B)) % count

    def run(self, baskets):
        baskets = list(baskets)
        support, size = self.support, self.bucket_count
        # Only the predicate count >= support matters; saturating is exact for
        # that predicate and lets support 50 use one byte per bucket.
        code = ('B' if support <= 255 else 'H' if support <= 65535
                else 'I' if support <= 2 ** 32 - 1 else 'Q')
        buckets = array(code, [0]) * size
        self.bucket_bytes = buckets.itemsize * size
        singles = Counter()
        ids = {}
        bucket_of = self._bucket
        for basket in baskets:
            items = sorted(set(basket))
            singles.update(items)
            for item in items:
                if item not in ids:
                    ids[item] = len(ids)
            for a, b in combinations(items, 2):
                h = bucket_of(ids[a], ids[b], size)
                if buckets[h] < support:
                    buckets[h] += 1

        bitmap = bytearray((size + 7) // 8)
        self.frequent_buckets = 0
        for h, count in enumerate(buckets):
            if count >= support:
                bitmap[h >> 3] |= 1 << (h & 7)
                self.frequent_buckets += 1
        self.bitmap_bytes = len(bitmap)
        del buckets  # release bucket counts BEFORE allocating pair counters
        frequent = {item for item, count in singles.items() if count >= support}
        del singles

        counts = Counter()
        self.peak_counters = 0
        for basket in baskets:
            items = sorted(set(basket).intersection(frequent))
            for pair in combinations(items, 2):
                h = bucket_of(ids[pair[0]], ids[pair[1]], size)
                if bitmap[h >> 3] & (1 << (h & 7)):
                    counts[pair] += 1
            self.peak_counters = max(self.peak_counters, len(counts))
        return {frozenset(pair): count for pair, count in counts.items()
                if count >= support}
