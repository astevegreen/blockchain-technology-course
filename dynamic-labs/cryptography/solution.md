## Lab Overview & Tone

This lab strips away the abstraction of "crypto magic" and forces students to interact directly with the cryptographic primitives that secure blockchains. By the end, students should intuitively understand the difference between hashing (integrity), encryption (confidentiality), and digital signatures (authentication).

---

## Part 1: Hashing & Entropy

### Phase 1 & 2: Hash Collisions & The Avalanche Effect
* **The Exploit (Phase 1):** The toy hash simply adds the ASCII values of the characters and applies modulo 16. Students can spoof the hash by adding arbitrary characters until the modulo aligns, or by swapping characters with offsetting ASCII values.
* **The Fix (Phase 2):** SHA-256 completely destroys this predictability. Changing a single bit of input changes roughly 50% of the output bits.
* **Discussion Point:** This demonstrates *Pre-image Resistance*. In a blockchain, if an attacker alters a historical transaction (even changing a single space), the block hash completely changes, instantly invalidating all subsequent blocks.

**Execution & Solutions:**
* **Phase 1 Solution:** The target hash for "PAY: ALICE | AMT: $100" is `15`. Any string that also hashes to 15 will trigger the success state.
  * *Command:* `toy_check PAY: ALICE | AMT: $100 ` (Just adding a space at the end changes the sum by 32, and $32 \pmod{16} = 0$, so it doesn't change the final hash.)
* **Phase 2 Execution:** * *Command:* `sha256 Deployment Alpha`
  * *Command:* `sha256 Deployment alpha` (Observe the radically different hex strings).

### Phase 3: Ransomware Cracking
* **The Exploit:** The student must convert the provided UTC string to a Unix timestamp (if they don't use the provided `1736670600`), subtract 60 to 300 seconds, and use the `hash_and_decrypt` command in batches of 10. 
* **Discussion Point:** Entropy (randomness) is the foundation of cryptography. The ransomware failed because it used a highly predictable seed (the system clock). This is analogous to why generating blockchain wallets requires highly secure, truly random numbers (CSPRNG), not just pseudo-random computer time.

**Execution & Solutions:**
* **The Math:** The file was saved at `1736670600`. The malware started 1-5 minutes (60-300 seconds) prior. The actual hardcoded offset is 124 seconds, making the target seed `1736670476`.
* **The Commands:** Students will need to scan down from the save time in chunks of 10.
  * *Command:* `hash_and_decrypt 1736670590 1736670600` (Fails)
  * ...
  * *Command:* `hash_and_decrypt 1736670470 1736670480` (Succeeds and outputs the decrypted brigade movement plans).

---

## Part 2: Merkle Trees

### Phase 4: Building the Tree
* **The Process:** Students must hash the raw strings, then concatenate the resulting hashes and hash them again. 
* **Common Pitfall:** Students often forget that concatenation is order-dependent. Hashing `(A + B)` produces a completely different result than hashing `(B + A)`. 

**Execution & Solutions:**
1. *Command:* `list_tx` (to view the 7 transactions).
2. Hash Tx0: `sha256 Tx0: Payroll -> Alice` -> Returns `Hash_A`.
3. Fill Leaf 0: `fill_leaf Leaf-0 <Hash_A>`.
4. Repeat for leaves 1 through 6. For leaf 7, they must duplicate Tx6 (standard Merkle tree balancing for odd numbers of leaves).
5. Combine L1: `combine L1-0 <Hash_A> <Hash_B>` -> Fills `L1-0`.
6. Repeat `combine <target_node> <hash_L> <hash_R>` moving up the tree until `ROOT` is filled.

### Phase 5: Merkle Proofs
* **The Forgery (Proof B):** The student is given a fake transaction string with an inflated payout ($50,000 instead of $5,000). However, the simulation provides them with the *real* sibling hashes from the valid tree. When they combine the fake transaction hash with the valid sibling hashes, the calculations will proceed smoothly until the final step, where it will completely fail to match the Official Root. 
* **Discussion Point:** This highlights logarithmic efficiency. A "Light Client" on a mobile phone doesn't need to download a 2MB block of 4,000 transactions; it only needs to download 12 sibling hashes to definitively prove its transaction is in the block.

**Execution & Solutions:**
1. *Command:* `get_proof B` (Outputs the fake Tx and the real sibling hashes).
2. Hash the fake Tx: `sha256 Tx: Contractor Payout #4402 ($50,000)` -> Returns `Fake_Hash`.
3. Combine with Sibling 1 (Left): `hash_pair <Sibling_1_Hash> <Fake_Hash>`.
4. Combine that result with Sibling 2 (Right) using `hash_pair`, and so on.
5. Compare the final computed root to the `Official Root` displayed on the dashboard. They will not match, proving the transaction is invalid.

---

## Part 3: Symmetric vs Asymmetric

### Key Distribution (Scenarios 1 & 2)
* **The Problem:** Symmetric encryption (AES) is incredibly fast but requires both parties to share the same secret key. Sending this key over the internet allows attackers to intercept it.
* **The Solution:** Hybrid cryptography. We use Asymmetric Public Keys to securely establish a secure channel, and then pass the Symmetric key through it.

**Execution & Solutions:**
* **Scenario 1 Commands:**
  * `view_record`
  * `verify_signature`
  * `encrypt_record asymmetric` (Solves the scenario while satisfying the public/private key policy for SSN data).
* **Scenario 2 Commands:**
  * `view_intercept`
  * `send_key_plaintext` (Demonstrates the insecure failure mode).
  * `send_key_encrypted` (Solves the key distribution problem).

### Identity & Bulk Data Transfer (Scenarios 3 & 4)
* **Signatures vs Encryption:** This is a critical conceptual hurdle. If Alice encrypts a file with Bob's public key, *only Bob* can read it (Confidentiality). If Alice signs a file with her own private key, *everyone* can read it, but they mathematically know it came from Alice (Authentication). 
* **Hybrid Cryptography:** Symmetric encryption is the right primitive for large files, while asymmetric encryption is the right primitive for distributing the symmetric key. Students should see why modern systems combine both methods.

**Execution & Solutions:**
* **Scenario 3 Commands:**
  * `view_cables`
  * `verify_cable A amb_public_key` (Returns INVALID).
  * `verify_cable B amb_public_key` (Returns VALID - this is the authentic cable).
  * `verify_cable C amb_public_key` (Returns INVALID).
* **Scenario 4 Commands:**
  * `send_file symmetric` (Fast, but leaves a raw key distribution problem).
  * `send_file asymmetric` (Fails because raw asymmetric encryption is not suitable for a 1GB payload).
  * `send_file hybrid` (Solves the scenario by combining fast symmetric encryption with asymmetric key exchange).
