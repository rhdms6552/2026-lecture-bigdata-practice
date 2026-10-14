# Observations

## Task 1
On the generated data at support 50, 1468->0 had confidence 0.8387, whereas 0->1468 had 0.0040; the first direction is the more reliable conditional prediction, because the antecedent supports differ.
The highest-confidence rule was 1468->0, with lift 1.2824; it improves on 0's baseline frequency on these baskets, but I would not treat a generated-data association as a causal or validated shopping recommendation.
Brute force over 2,000 items needs 1,999,000 pair counters; pass one retains 1,849 items (1,708,476 possible pairs), and Apriori allocates 820,259 observed-pair counters after pruning.

## Task 2
The default data still fit at support 1 (327.0 MB); with 10,000 items/80,000 baskets I stopped at support 25 after 39.28s and 817.3 MB because the 512 MiB traced-memory budget was reached, not because the OS ran out of memory.
For support 400->200->100->50, counters grew 5.54x/4.67x/3.00x per halving; from 25 to 1 they plateaued at 893,456, since all observed pairs were already candidates.
At support 50, 820,259 counters found only 6,397 answers (128.2 counters/answer); below 25 the counters stayed fixed while answers grew from 17,045 to 893,456, so a lower threshold can inflate candidate overhead first and output size later.

## Task 3
I chose 1,048,576 buckets; threshold-saturated byte counters cost 1 MiB, and the packed bitmap costs 128 KiB (both coexist briefly); deleting the counters before pass two reduced pair counters from 820,259 to 13,109, with exactly the same pairs and supports.
Including metadata and outputs, traced peaks were 102.57 MB plain versus 3.97 MB PCY; the sampled memory crossover was between 2,000 and 5,000 baskets at support 50, and depends on support, item distribution, and bucket count.
Shrinking to 4,096 buckets raised pair counters to 820,259 and traced peak to 102.89 MB: collisions made the bitmap admit too many pairs; reducing the bucket array alone did not reduce total memory.
