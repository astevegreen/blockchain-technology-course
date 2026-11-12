**Background:** To scale up the network, we want to publish completed transaction blocks without revealing every detail publicly, while still allowing users to verify if specific transactions exist. A **Merkle Tree** is the solution.

**Your Task:** Manually construct a 3-level Merkle Tree by hashing the transactions and combining them up to the root.

The tree has 8 leaf slots even though `list_tx` shows 7 transactions. This
is intentional: when a Merkle tree has an odd number of leaves, duplicate the
final transaction hash into the last slot so the bottom layer can be paired
cleanly.

**Available Commands:**
- `list_tx` - View raw transactions
- `sha256 <txt>` - Generate hash
- `fill_leaf <Leaf-0..Leaf-7> <hash>` - Populate the bottom layer
- `combine <target_node> <hash_L> <hash_R>` - Build a specific parent node

**Examples:**
- `fill_leaf Leaf-0 <hash>` - Fill the first leaf
- `fill_leaf Leaf-7 <Leaf-6 hash>` - Duplicate the final transaction hash
- `combine L1-0 <Leaf-0 hash> <Leaf-1 hash>` - Build the first Level 1 parent
- `combine ROOT <L2-0 hash> <L2-1 hash>` - Finish the tree

Click any filled node to copy its full hash for the next command.
