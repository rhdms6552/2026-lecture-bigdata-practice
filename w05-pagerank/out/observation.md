# Observations

## Task 1
The broken version omits a dead end's rank from the next vector, so the sample graph drains to zero; I instead redistribute all dangling mass uniformly across every node, preserving total rank 1.
The update adds [(1-beta) + beta*dangling_mass]/n to each node: dangling redistribution replaces lost mass, while uniform teleportation lets the surfer leave a spider trap; the broken trap takes 100%, but the repaired graph keeps A=0.0375 and B=0.069375.
Beta is the probability of following an outgoing link; with probability 1-beta the surfer jumps to a uniformly chosen node, and at a dead end I also choose a uniformly random destination.

## Task 2
For 1,200 nodes and tol=1e-10, beta 0.5/0.7/0.85/0.95/0.99 required 14/17/20/23/24 iterations: less teleportation weakens contraction, although this graph's increase near 1 was modest; tightening tol from 1e-3 to 1e-10 added 13 iterations, about 1.86 per digit.
At beta=0.85, growing 1,200 to 20,000 nodes changed 20 to 21 iterations but 0.0135s to 0.2499s (18.5x); mixing controls the iteration count, while each pass must visit more nodes and edges.
The first tested top-10 order change was beta=0.7, where p00004 overtook p00000; membership stayed unchanged, so a published ranking should disclose beta and test whether close positions survive that choice.

## Task 3
I store integer adjacency lists and two rank vectors, using O(n+E) total space and a conservative 2n+12 float-slot bound: 2,412 versus 1,440,000 at n=1,200 (597.0x fewer), with 87.8x measured speedup.
Teleportation and dangling redistribution contribute the same scalar to every node, so filling a length-n vector costs O(n); following only actual edges costs O(E), and neither requires an n-by-n matrix.
Worst per-node difference from dense was 1.17e-15, caused by floating-point summation order and regrouping dangling contributions, well below 1e-9; the sparse version also solved 200,000 nodes in 2.27s, where a dense float64 matrix alone would need 320 GB.
