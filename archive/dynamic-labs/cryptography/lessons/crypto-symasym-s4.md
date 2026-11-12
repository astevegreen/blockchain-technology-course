**Background:** You successfully encrypted a tiny text record using Asymmetric encryption in Scenario 1. Now, you need to securely transmit a massive 1GB ISR (Intelligence, Surveillance, and Reconnaissance) drone video.

**The Problem:** You do not have access to a secure cloud relay. You must encrypt the video locally before sending it over the wire.

**Your Task:**
1. Attempt to send the 1GB video file using pure Symmetric encryption.
2. Attempt to send the 1GB video file using pure Asymmetric encryption.
3. Determine the correct cryptographic architecture to secure bulk data payloads.

**Available Commands:**
- `send_file <symmetric|asymmetric|hybrid>`

---

**Key Concepts:**
- **Payload Constraints**: RSA can only encrypt data smaller than its key size. It is not designed for bulk data.
- **Hybrid Cryptography**: Use Symmetric crypto for the data payload (speed/size), and Asymmetric crypto for the key exchange (security). This is how TLS/HTTPS secures internet traffic.
