# Applied Cryptography & Identity

Welcome. In this lab you'll work hands-on with the cryptographic primitives that secure distributed ledgers and digital identity: **hashing**, **Merkle trees**, and **symmetric vs. asymmetric encryption**.

## How to use this interface

- Use the **sidebar on the left** to move between the three lab parts.
- Each part loads an interactive terminal. Type commands into the input box and press **Enter** to run them.
- Your **progress bar** at the top of each page tracks completion of that part's phases. Aim for 100% before moving to the next part.
- Output history scrolls below the input box. Re-read it whenever you get stuck — earlier output usually contains the data you need next.
- Type `help` for examples, press **Up Arrow** to recall previous commands, press **Tab** to complete command names, and click highlighted hashes to copy them.

---

## Part 1: Hashing & Entropy
Open **1. Hashing** in the sidebar.

### Phase 1: Weak Hash Collisions
You are analyzing a legacy financial system that relies on a weak 4-bit hash.
**Task:** Using the terminal, attempt to forge a fraudulent transaction that results in the exact same hash output as the target valid transaction.
* Use `toy_hash <text>` to test inputs.
* Use `toy_check <text>` to submit your forgery.

### Phase 2: The Avalanche Effect
The system has been upgraded to SHA-256.
**Task:** Verify the integrity of the new algorithm. Hash a baseline string, then change exactly one character (e.g., capitalize a letter). Observe how the resulting hexadecimal string changes completely.

### Phase 3: Entropy & Ransomware
An endpoint was encrypted by 'TimeLock' ransomware, which seeds its encryption keys using the Unix Timestamp of when the process started. You know the exact second the file was saved.
**Task:** Calculate the time window (1–5 minutes prior to the save time) and use the `hash_and_decrypt <start_ts> <end_ts>` command to brute-force the seed and recover the data.

**Discussion Questions:**
1. Why is the "Avalanche Effect" critical for ensuring transaction immutability in a blockchain ledger?
2. In Phase 3, what specific weakness in the ransomware's design allowed you to crack the encryption key without a supercomputer?

---

## Part 2: Merkle Trees (Data Verification)
Open **2. Merkle Trees** in the sidebar.

### Phase 4: Building the Tree
To scale the network, the organization is implementing Merkle Trees to batch transactions.
**Task:** Manually construct a 3-level Merkle Tree.
1. Use `list_tx` to see the base data.
2. Hash the transactions and use `fill_leaf <Leaf-0..Leaf-7> <hash>` to populate the bottom layer.
3. Use `combine <target_node> <hash_L> <hash_R>` to build each parent node, for example `combine L1-0 <Leaf-0 hash> <Leaf-1 hash>`.

### Phase 5: Verifying a Merkle Proof
Two transactions have been flagged for review. One is valid, and one is a forgery that shares the same Merkle Root.
**Your Task:** Run `get_proof A` and `get_proof B`. Manually step through the provided sibling hashes for both proofs, combining them locally to see which path mathematically resolves to the correct Root and which one breaks.

**Discussion Questions:**
1. If a block contains 4,096 transactions, how many hashes do you need to download to verify your specific transaction is included?
2. In Proof B, how was the attacker attempting to spoof the validation process?

---

## Part 3: Symmetric vs Asymmetric Cryptography
Open **3. Symmetric and Asymmetric Encryption** in the sidebar.

### Phase 6: Confidentiality vs Authentication
Work through Scenarios 1 through 4 in the interactive terminal. You will manage public/private keypairs, orchestrate secure key distribution, identify forged organizational announcements, and analyze network scaling constraints.

**Task:** Complete all four scenarios until the progress bar reaches 100%. Pay close attention to when the terminal informs you that a message is readable versus when it is verifiable.

**Discussion Questions:**
1. Why does a digital signature provide *Authentication* and *Non-Repudiation*, but completely fail to provide *Confidentiality*?
2. In the final scenario, why are blockchain transactions explicitly signed but never encrypted?
