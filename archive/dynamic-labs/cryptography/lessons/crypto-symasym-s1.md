**Background:** A single Soldier's personnel record was leaked to a shared drive. The S1 Officer assumed that digitally signing the file made it secure.

**The Policy:** HQ has just released a new directive: *All files containing an SSN must be protected using Public/Private key infrastructure.*

**Your Task:**
1. View the record and its signature
2. Verify the signature is authentic
3. Properly secure the file using the architecture mandated by HQ.

**Available Commands:**
- `view_record` - See the signed file
- `verify_signature` - Check if the signature is valid
- `encrypt_record <symmetric|asymmetric|hybrid>` - Apply encryption

---

**Key Concepts:**
- **Digital Signature**: Proves WHO signed (authentication) but doesn't provide confidentiality.
- **Asymmetric Encryption**: Ideal for securing small data payloads (like a single text record) while completely avoiding Symmetric key management overhead.
