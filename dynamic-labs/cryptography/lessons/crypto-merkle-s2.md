**Background:** The Merkle Tree is now in production! However, two transactions have been flagged for review. One of them is a forgery.

**Your Task:** Verify the provided Merkle Proofs for transactions A and B. Manually step through the provided sibling hashes, combining them locally to see which path resolves to the Official Root and which one breaks.

**Available Commands:**
- `get_proof <A|B>` - Get the transaction data and sibling hashes
- `hash_pair <hash_L> <hash_R>` - Combine hashes manually without spaces
