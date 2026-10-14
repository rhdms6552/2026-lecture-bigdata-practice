# PCY memory accounting and rule evidence

## Rules and candidate counts

At support 50 on the generated dataset, the highest-confidence rule (ties sorted by item ID) was **1468 -> 0**, confidence 0.838710, lift 1.282431; reverse confidence 0.003976. Antecedent support was 62, consequent support 13080, out of 20,000 baskets. Its lift compares the prediction to the consequent's baseline frequency, so high confidence alone is not sufficient evidence of a useful relationship. These are associations in generated data, not causal claims or validated retail recommendations.

All pairs among 2,000 items would require 1,999,000 counters. Pass one leaves 1,849 frequent singletons, hence 1,708,476 possible survivor pairs. The sparse baseline actually allocates counters only for 820,259 observed survivor pairs. These are three different counts.

## Bucket memory is included

PCY uses 1,048,576 buckets. During pass one, counts saturate at support: values beyond 50 cannot change whether a bucket is frequent. `array('B')` therefore stores each bucket in one byte at support 50, for **1,048,576 payload bytes (1 MiB)**. Larger supports select wider integer types. Saturation cannot hide a frequent pair: its bucket total is at least its own count, so it always reaches the threshold.

The bitmap is packed into **131,072 bytes (128 KiB)**. Bucket counts and bitmap coexist briefly during conversion (1,179,648 payload bytes); the counts array is then deleted before pair counters are allocated. Singleton counts, ID mapping, sets, dictionary keys, output, and allocation overhead are all included in the separately measured tracemalloc peak below. The harness's `peak_counters` counts pair-specific counting entries, not bucket slots or physical bytes; a 98.4% counter reduction alone would not prove the same percentage of byte savings.

At 20,000 baskets, total traced allocation peaks were **102.568 MB for plain Apriori** versus **3.966 MB for PCY**, a 25.86x ratio. PCY is slower in the untraced benchmark because it hashes pairs in both passes. This task scores memory, not speed.

## Crossover with a fixed support of 50

All prefixes come from the same generated 20,000-basket dataset; comparisons verify the entire answer dictionary, including support counts.

| Baskets | Plain peak MB | PCY peak MB | Plain pair counters | PCY pair counters |
|---:|---:|---:|---:|---:|
| 100 | 0.056 | 1.277 | 0 | 0 |
| 500 | 0.111 | 1.385 | 136 | 12 |
| 1,000 | 0.191 | 1.405 | 1,078 | 59 |
| 2,000 | 0.834 | 1.438 | 6,228 | 182 |
| 5,000 | 6.494 | 1.520 | 50,168 | 903 |
| 20,000 | 102.568 | 3.966 | 820,259 | 13,109 |

The sampled byte-memory crossover lies **between 2,000 and 5,000 baskets**: plain is smaller at 2,000, PCY smaller at 5,000. This range is specific to support 50, this distribution, the 2,000-item universe, and the chosen bucket count. Fewer buckets reduce fixed array cost but increase collisions; more distinct items, larger baskets, support, and skew all change the crossover.

## Smaller bucket arrays

20,000 baskets, support 50; all variants return exactly the same pairs and counts.

| Buckets | Frequent buckets | Bucket bytes | Bitmap bytes | Pair counters | Whole traced peak MB |
|---:|---:|---:|---:|---:|---:|
| 1,048,576 | 6,972 | 1,048,576 | 131,072 | 13,109 | 3.966 |
| 65,536 | 21,468 | 65,536 | 8,192 | 305,445 | 30.110 |
| 4,096 | 4,096 | 4,096 | 512 | 820,259 | 102.890 |

A small array combines many unrelated pairs into each bucket. Those buckets become frequent even if most individual pairs are not, so the bitmap admits more candidates and the pass-two dictionary grows. The 1,048,576-bucket choice is a measured tradeoff that filters well here, not a universally optimal size.
