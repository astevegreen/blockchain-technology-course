**Background:** During a crisis, three diplomatic cables have been received, all bearing digital signatures claiming to be from the US Ambassador. Intelligence indicates that an adversary is injecting forged cables into the network to cause chaos.

**The Problem:** You must identify which cable is authentic before executing the orders.

**Your Task:**
1. View all three cables
2. Verify the signatures by explicitly checking them against the Ambassador's known public key
3. Identify the authentic order

**Available Commands:**
- `view_cables` - See all three cables
- `verify_cable <A|B|C> <public_key_reference>` - Verify a specific cable (e.g., use `amb_public_key`)

---

**Key Concepts:**
- **Digital Signatures**: Only the private key holder can create a valid signature.
- **Non-Repudiation**: The signer cannot later deny sending the message.
- **Authentication**: Proves the message mathematically originated from the claimed sender.
