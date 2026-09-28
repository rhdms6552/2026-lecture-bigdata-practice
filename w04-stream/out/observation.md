# Observations

## Task 1
Bloom insertion only sets bits and membership checks those same bits, so an inserted item cannot become a false negative; predicted false positives were 0.860%, measured 0.900% on 20,000 absent queries, a small sampling difference.
I used the mean of eight group medians for FM: 26,624 / 19,953 = 1.334x; on the same hashes the plain mean gave 60,064 (3.010x) and median 16,384 (0.821x), showing how large hash maxima distort the mean.
Reservoir sampling draws j = rng.randrange(n) for each new item and replaces only when j < k: arrival chance k/n and later survival give every stream position final probability k/N, without knowing N or holding more than k items.

## Task 2
At 6,400,000 items, exact counting took 109.18s and 207.087 MB of traced memory; I stopped because this exceeded a one-minute interactive time budget, although the run completed without exhausting RAM.
Across 64x more input, exact memory grew 49.08x (roughly O(n), measured slope 0.936); FM stayed at 8,601-8,603 bytes (O(64), effectively O(1)); FM ratios were 1.032x, 1.449x, 1.087x, 0.976x with no reliable improvement from more input.
A factor of two can answer whether daily distinct traffic is roughly thousands or millions for capacity planning, but is inadequate for per-user billing or deciding whether visitors grew by 5%.

## Task 3
For p(k) = (1 - exp(-kn/m))^k, setting d(log p)/dk = 0 gives kn/m = ln(2), so k = (m/n)ln(2) = 6.93 at 10 bits/item; I changed k from 1 to 7 (the optimum is still 7 after reserving metadata).
The ideal Bloom floor is exp(-10 ln(2)^2) = 0.8193%; my 78,872 payload bits plus metadata use 80,000 bits and predict 0.8774%; measured 0.8785% with zero false negatives is close, within the 0.9% strong threshold.
If n is unknown, monitor occupancy and add a new Bloom layer when memory may grow, assigning per-layer error budgets; underestimating n saturates the bits and raises false positives, while overestimating n wastes reserved space; with a fixed total budget, use an explicit window/reset policy and promise membership only within that window.
