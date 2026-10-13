# Prediction before Task 2 measurements

At fixed beta and tolerance, I expect the iteration count to stay in a similar range when growing the generated graph from 1,200 to 20,000 nodes. Graph structure and the transition operator's contraction matter more than node count alone; the counts need not match exactly.
I expect wall time to increase because each iteration traverses more nodes and edges. Higher beta should usually slow convergence, since teleportation mixes less strongly; tighter tolerance should require additional iterations.
