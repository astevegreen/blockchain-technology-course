**Background:** You need to send classified extraction coordinates to a local national collaborator. You have successfully encrypted the file with Symmetric Encryption (AES-256), but the collaborator needs the Symmetric Key to decrypt it.

**The Problem:** You are operating over a monitored, unclassified network. If you send the key in plaintext, adversary SIGINT will intercept it.

**Your Task:**
1. View the encrypted intercept
2. Try sending the key in plaintext to see what happens
3. Figure out how to send the Symmetric Key securely using Asymmetric cryptography

**Available Commands:**
- `view_intercept` - See the encrypted message
- `send_key_plaintext` - Try sending the key (insecure!)
- `send_key_encrypted` - Securely transmit the key

---

**Key Concepts:**
- **The Key Distribution Problem**: How do you securely share a symmetric key over an insecure channel?
- **Public Key Infrastructure (PKI)**: Anyone can encrypt data using a public key, but only the holder of the paired private key can decrypt it.
