#!/usr/bin/env python3
"""Week 7 · Task 1 — k-means, and the thing that decides the answer.

Textbook §7.1 (clustering, the curse of dimensionality), §7.3 (k-means).

k-means is four lines: pick centroids, assign every point to the nearest one,
move each centroid to the mean of its points, repeat. It always converges.

It converges to a **local** optimum, and which one depends entirely on where you
started. That is not a footnote - it is the difference between a clustering that
means something and one that does not, and you can watch it happen on nine points.

    python3 task1_kmeans.py --verify
"""
import argparse, math, random

# Three obvious blobs of three points each. Any sensible clustering finds them.
BLOBS = [(0.0, 0.0), (0.2, 0.1), (0.1, 0.2),
         (8.0, 8.0), (8.2, 8.1), (8.1, 8.2),
         (0.0, 8.0), (0.2, 8.1), (0.1, 8.2)]


def euclidean(a, b):
    """Distance between two points of any dimension."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


def assign(points, centroids):
    """Nearest centroid for each point. Return a list of centroid indices.

    Ties go to the lower index, so that everybody's answer is the same.
    """
    return [min(range(len(centroids)), key=lambda j: euclidean(p, centroids[j]))
            for p in points]


def update(points, labels, k, previous=None):
    """Move each centroid to the mean of its points.

    An empty cluster has no mean. Decide what you do - and say so, because the
    choice changes the result and there is more than one defensible answer.
    """
    groups = [[] for _ in range(k)]
    for point, label in zip(points, labels):
        groups[label].append(point)
    # Keep an empty cluster in place. Standalone calls without old centres
    # use the first input point as a deterministic fallback.
    return [tuple(sum(axis) / len(group) for axis in zip(*group)) if group
            else (previous[j] if previous is not None else points[0])
            for j, group in enumerate(groups)]


def kmeans(points, k, init="random", seed=246, max_iter=100):
    """Run to convergence. Return (labels, centroids, sse).

    `sse` is the sum over points of the squared distance to their own centroid.
    It is what k-means minimises, and it is how you compare two runs.

    `init` is either:
        "random"   pick k points at random as the starting centroids
        "++"       k-means++ (§7.3.2): pick the first at random, then pick each
                   next one with probability proportional to the squared distance
                   to the nearest centroid already chosen

    Set `kmeans.iterations` to how many passes you used.
    """
    if not 1 <= k <= len(points) or max_iter < 1:
        raise ValueError("need 1 <= k <= number of points and max_iter >= 1")
    rng = random.Random(seed)
    if init == "random":
        centroids = rng.sample(points, k)
    elif init == "++":
        chosen = [rng.randrange(len(points))]
        nearest_sq = [math.inf] * len(points)
        while len(chosen) < k:
            last = points[chosen[-1]]
            nearest_sq = [min(old, euclidean(p, last) ** 2)
                          for p, old in zip(points, nearest_sq)]
            if any(nearest_sq):
                chosen.append(rng.choices(range(len(points)), weights=nearest_sq)[0])
            else:
                # Every remaining location is a duplicate of a chosen one.
                chosen.append(next(i for i in range(len(points)) if i not in chosen))
        centroids = [points[i] for i in chosen]
    else:
        raise ValueError("init must be 'random' or '++'")

    labels = None
    for kmeans.iterations in range(1, max_iter + 1):
        new_labels = assign(points, centroids)
        if new_labels == labels:
            break
        labels = new_labels
        centroids = update(points, labels, k, centroids)
    return labels, centroids, sse_of(points, labels, centroids)


def sse_of(points, labels, centroids):
    """Sum of squared distances from each point to its assigned centroid."""
    return sum(euclidean(p, centroids[label]) ** 2 for p, label in zip(points, labels))


# ------------------------------------------------------------------- harness
def verify():
    fails = 0

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<50} {detail}")
        fails += not ok

    try:
        check("distance in 2d", abs(euclidean((0, 0), (3, 4)) - 5) < 1e-9)
        check("distance in 5d",
              abs(euclidean((0,) * 5, (1,) * 5) - math.sqrt(5)) < 1e-9)
    except NotImplementedError:
        print("  euclidean is still a stub"); return 1

    try:
        labels, cents, sse = kmeans(BLOBS, 3, init="++", seed=1)
    except NotImplementedError:
        print("  kmeans is still a stub"); return 1

    groups = {}
    for p, l in zip(BLOBS, labels):
        groups.setdefault(l, []).append(p)
    check("three clusters of three", sorted(len(g) for g in groups.values()) == [3, 3, 3],
          sorted(len(g) for g in groups.values()))
    check("the three blobs were recovered",
          all(max(q[0] for q in g) - min(q[0] for q in g) < 1 and
              max(q[1] for q in g) - min(q[1] for q in g) < 1
              for g in groups.values()))
    check("sse is small when clusters are right", sse < 1.0, f"sse {sse:.4f}")

    # Bad luck with random starts should sometimes be visibly worse.
    randoms = [kmeans(BLOBS, 3, init="random", seed=s)[2] for s in range(40)]
    plusplus = [kmeans(BLOBS, 3, init="++", seed=s)[2] for s in range(40)]
    check("random init sometimes lands badly", max(randoms) > min(randoms) * 5,
          f"sse from {min(randoms):.3f} to {max(randoms):.3f}")
    check("k-means++ is more reliable than random",
          sum(plusplus) / len(plusplus) <= sum(randoms) / len(randoms),
          f"mean sse: ++ {sum(plusplus) / len(plusplus):.3f} vs "
          f"random {sum(randoms) / len(randoms):.3f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
