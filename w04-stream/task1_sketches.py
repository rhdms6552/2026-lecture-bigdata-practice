#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse, hashlib, math, random, statistics, struct


def hash_words(item, count, seed):
    """Stable, seeded 64-bit hash outputs; never retain input items."""
    data = str(seed).encode() + b"\0" + str(item).encode()
    return struct.unpack("<" + "Q" * count,
                         hashlib.shake_256(data).digest(8 * count))


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        if m <= 0 or k <= 0:
            raise ValueError("m and k must be positive")
        self.m, self.k, self.seed = m, k, seed
        self.bits = bytearray((m + 7) // 8)

    def _indices(self, item):
        return (h % self.m for h in hash_words(item, self.k, self.seed))

    def add(self, item):
        for i in self._indices(item):
            self.bits[i // 8] |= 1 << (i % 8)

    def __contains__(self, item):
        return all(self.bits[i // 8] & (1 << (i % 8))
                   for i in self._indices(item))

    def expected_fp_rate(self, n_inserted):
        """The textbook's predicted false-positive rate after n insertions.

        §4.4.2 derives it. Return the number, do not measure it - the harness
        measures separately and compares the two.
        """
        if n_inserted < 0:
            raise ValueError("n_inserted must be nonnegative")
        return (-math.expm1(-self.k * n_inserted / self.m)) ** self.k


def fm_registers(stream, n_hashes=64, seed=246):
    """One maximum trailing-zero count per hash, plus empty-stream state."""
    if n_hashes <= 0:
        raise ValueError("n_hashes must be positive")
    maxima = [-1] * n_hashes
    prefix = str(seed).encode() + b"\0"
    offsets = tuple(range(0, 8 * n_hashes, 8))
    byte_zeros = tuple((b & -b).bit_length() - 1 if b else 8
                       for b in range(256))
    for item in stream:
        digest = hashlib.shake_256(prefix + str(item).encode()).digest(8 * n_hashes)
        for i, offset in enumerate(offsets):
            zeros = byte_zeros[digest[offset]]
            # Read additional bytes only when the low byte is all zeros.
            # This is exactly the same 64-bit hash as hash_words(), with
            # fewer temporary Python integers during memory profiling.
            if zeros == 8:
                for j in range(1, 8):
                    extra = byte_zeros[digest[offset + j]]
                    zeros += extra
                    if extra < 8:
                        break
            if zeros > maxima[i]:
                maxima[i] = zeros
    return maxima


def combine_fm(maxima):
    """Average eight group medians to suppress extreme hash outliers."""
    if maxima[0] < 0:
        return 0.0
    estimates = [float(2 ** r) for r in maxima]
    groups = min(8, len(estimates))
    return statistics.mean(statistics.median(estimates[g::groups])
                           for g in range(groups))


def flajolet_martin(stream, n_hashes=64, seed=246):
    """Estimate how many DISTINCT items went past, in almost no memory.

    §4.5. Hash each item, count trailing zeros in the hash, keep the maximum.
    A maximum of R suggests about 2^R distinct items, because seeing R trailing
    zeros is a 1-in-2^R event.

    One hash gives an estimate with enormous variance, so you use many and
    combine them. How you combine them matters a great deal:

      * averaging 2^R directly is dominated by whichever hash got lucky - the
        values are exponential, so one outlier swamps the rest
      * the median is robust but can only ever be a power of two
      * §4.5.3 suggests grouping, and combining twice

    The harness accepts anything **within a factor of two** of the truth. That is
    not a generous tolerance, it is an honest one: this method really is that
    crude, and HyperLogLog exists because of it. Getting inside a factor of two
    reliably is the requirement; getting closer than that is not expected here.

    Return your estimate as a float.
    """
    return combine_fm(fm_registers(stream, n_hashes, seed))


def reservoir_sample(stream, k, seed=246):
    """Keep k items uniformly at random from a stream of unknown length.

    §4.3. Every item that went past must end up with the same probability k/n
    of being in your sample, and you only ever hold k of them.

    Return a list of k items (or fewer if the stream was shorter).
    """
    if k < 0:
        raise ValueError("k must be nonnegative")
    if k == 0:
        return []
    rng = random.Random(seed)
    sample = []
    for n, item in enumerate(stream, 1):
        if n <= k:
            sample.append(item)
        else:
            j = rng.randrange(n)
            if j < k:
                sample[j] = item
    return sample


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {detail}")
        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(m=8192, k=5)
    except NotImplementedError:
        print("  BloomFilter is still a stub"); return 1
    inserted = [f"item-{i}" for i in range(800)]
    for x in inserted:
        bf.add(x)
    check("no false negatives", all(x in bf for x in inserted))

    absent = [f"other-{i}" for i in range(20_000)]
    fp = sum(1 for x in absent if x in bf) / len(absent)
    predicted = bf.expected_fp_rate(len(inserted))
    close = abs(fp - predicted) < max(0.02, predicted * 0.5)
    check("measured false-positive rate matches theory", close,
          f"measured {fp:.3%}, predicted {predicted:.3%}")

    # --- Flajolet-Martin: a factor of two is what this method gives you
    try:
        distinct = 20_000
        stream = [f"k{rng.randrange(distinct)}" for _ in range(120_000)]
        est = flajolet_martin(stream)
    except NotImplementedError:
        print("  flajolet_martin is still a stub"); return 1
    true_distinct = len(set(stream))
    ratio = est / true_distinct
    check("distinct estimate within a factor of 2", 0.5 <= ratio <= 2.0,
          f"estimated {est:,.0f}, true {true_distinct:,} ({ratio:.2f}x)")

    # --- Reservoir: uniform over many trials
    try:
        counts = [0] * 20
        trials = 4000
        for t in range(trials):
            s = reservoir_sample(range(20), 5, seed=t)
            for i in s:
                counts[i] += 1
    except NotImplementedError:
        print("  reservoir_sample is still a stub"); return 1
    expected = trials * 5 / 20
    spread = (max(counts) - min(counts)) / expected
    check("reservoir is uniform across items", spread < 0.15,
          f"spread {spread:.1%} around {expected:.0f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
