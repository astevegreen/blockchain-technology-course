import hashlib
import random
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class LabCore:
    def __init__(self):
        # ==========================================
        # MODULE 1: HASHING & ENTROPY
        # ==========================================
        self.toy_target_msg = "PAY: ALICE | AMT: $100"
        self.toy_target_hash = self.toy_hash_4bit(self.toy_target_msg)

        # Ransomware variables
        self.malware_family = "linux.encoder"
        self.file_mod_time_unix = 1736670600
        self.file_mod_time_str = "2025-01-12 08:30:00 UTC"
        self.malware_start_time = self.file_mod_time_unix - 124
        self.ransom_key = hashlib.sha256(
            str(self.malware_start_time).encode()
        ).hexdigest()
        self.secret_data = "CONFIDENTIAL: BRIGADE MOVEMENT PLANS [DECRYPTED]"

        self.ransom_note = """
====================================================================
!!! YOUR FILES HAVE BEEN ENCRYPTED !!!
====================================================================
All critical brigade movement plans have been secured using 
military-grade AES-256 encryption. 

To restore your systems, you must send 5 BTC to the following address:
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

Do NOT attempt to modify the files or use third-party recovery tools.
Doing so will permanently destroy your data.

Your personal decryption ID is: 84a9b2c7-f12a-4b9e-9d21-3f8c2b7a9e10
(Note: This ID is for tracking your payment, it is NOT the key)
====================================================================
"""

        # ==========================================
        # MODULE 2.1: SMALL TREE (Build it yourself)
        # ==========================================
        self.merkle_txs = [
            "Tx0: Payroll -> Alice",
            "Tx1: Payroll -> Bob",
            "Tx2: Payroll -> Charlie",
            "Tx3: Expense -> Dave",
            "Tx4: Expense -> Eve",
            "Tx5: Expense -> Frank",
            "Tx6: Contract -> Grace",
        ]
        self.leaves = [self.sha256_hash(tx) for tx in self.merkle_txs]
        self.leaves.append(self.leaves[-1])
        self.level1 = [
            self.sha256_hash(self.leaves[i] + self.leaves[i + 1])
            for i in range(0, 8, 2)
        ]
        self.level2 = [
            self.sha256_hash(self.level1[i] + self.level1[i + 1])
            for i in range(0, 4, 2)
        ]
        self.root = self.sha256_hash(self.level2[0] + self.level2[1])

        self.student_leaves = [None] * 8
        self.student_level1 = [None] * 4
        self.student_level2 = [None] * 2
        self.student_root = None

        # ==========================================
        # MODULE 2.2: LARGE TREE
        # ==========================================
        self.lg_leaves_valid = []
        for i in range(16):
            self.lg_leaves_valid.append(
                self.sha256_hash(f"ValidTx_{i}_{random.random()}")
            )

        self.proof_a_tx = "Tx: Supply Purchase Order #9921"
        self.lg_leaves_valid[2] = self.sha256_hash(self.proof_a_tx)

        original_tx_b = "Tx: Contractor Payout #4402 ($5,000)"
        self.lg_leaves_valid[13] = self.sha256_hash(original_tx_b)

        self.lg_L3 = [
            self.sha256_hash(self.lg_leaves_valid[i] + self.lg_leaves_valid[i + 1])
            for i in range(0, 16, 2)
        ]
        self.lg_L2 = [
            self.sha256_hash(self.lg_L3[i] + self.lg_L3[i + 1]) for i in range(0, 8, 2)
        ]
        self.lg_L1 = [
            self.sha256_hash(self.lg_L2[i] + self.lg_L2[i + 1]) for i in range(0, 4, 2)
        ]
        self.lg_official_root = self.sha256_hash(self.lg_L1[0] + self.lg_L1[1])

        self.proof_a_siblings = [
            {"pos": "right", "hash": self.lg_leaves_valid[3]},
            {"pos": "left", "hash": self.lg_L3[0]},
            {"pos": "right", "hash": self.lg_L2[1]},
            {"pos": "right", "hash": self.lg_L1[1]},
        ]

        self.proof_b_tx = "Tx: Contractor Payout #4402 ($50,000)"
        self.proof_b_siblings = [
            {"pos": "left", "hash": self.lg_leaves_valid[12]},
            {"pos": "right", "hash": self.lg_L3[7]},
            {"pos": "left", "hash": self.lg_L2[2]},
            {"pos": "left", "hash": self.lg_L1[0]},
        ]

        # ==========================================
        # MODULE 3: CRYPTOGRAPHY & IDENTITY
        # ==========================================
        self.scenario_state = {
            "s1_record_secured": False,
            "s1_completed": False,
            "s2_key_sent_securely": False,
            "s2_completed": False,
            "s3_ambassador_verified": False,
            "s3_completed": False,
            "s4_video_sent": False,
            "s4_completed": False,
        }

        # Scenario 1: Leaked S1 Record
        self.s1_record_text = "CONFIDENTIAL PERSONNEL RECORD | SGT John Doe | SSN: 000-00-0000 | Clearance: TS/SCI"
        self.s1_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.s1_public_key = self.s1_private_key.public_key()
        self.s1_record_signature = self._sign(self.s1_record_text, self.s1_private_key)

        # Scenario 2: Embassy Collaborator Key Exchange
        self.collab_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.collab_public_key = self.collab_private_key.public_key()
        self.secret_message = "CLASSIFIED: Extraction point moved to Coordinates 34.12, -118.40. Await further instructions."
        self.symmetric_key = os.urandom(32)
        self.encrypted_message = self._symmetric_encrypt(
            self.secret_message, self.symmetric_key
        )

        # Scenario 3: Forged Ambassador Cables
        self.amb_private = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.amb_public = self.amb_private.public_key()
        self.imposter_private = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        self.cables = {
            "A": {
                "text": "CABLE A: Embassy evacuation protocol initiated. All non-essential personnel report to the staging area.",
                "key": self.imposter_private,
            },
            "B": {
                "text": "CABLE B: Host nation negotiations successful. Resume normal embassy operations immediately.",
                "key": self.amb_private,
            },
            "C": {
                "text": "CABLE C: Immediate authorization granted to surrender compound to local militia forces.",
                "key": self.imposter_private,
            },
        }

        self.signed_cables = {}
        for c_id, c_data in self.cables.items():
            self.signed_cables[c_id] = {
                "text": c_data["text"],
                "signature": self._sign(c_data["text"], c_data["key"]),
            }

    def template_ctx(self) -> dict:
        """Values that lessons/*.md may interpolate via str.format."""
        return {
            "toy_target_msg": self.toy_target_msg,
            "toy_target_hash": self.toy_target_hash,
            "file_mod_time_str": self.file_mod_time_str,
        }

    # ==========================================
    # INTERNAL PRIMITIVES
    # ==========================================
    def toy_hash_4bit(self, s):
        return sum(ord(c) for c in s) % 16

    def check_toy_collision(self, s):
        h = self.toy_hash_4bit(s)
        return (h == self.toy_target_hash and s != self.toy_target_msg), h

    def sha256_hash(self, s):
        return hashlib.sha256(s.encode()).hexdigest()

    def get_ransom_note(self):
        return self.ransom_note

    def attempt_decrypt(self, ts):
        if hashlib.sha256(str(ts).encode()).hexdigest() == self.ransom_key:
            return True, self.secret_data
        return False, "[DECRYPTION FAILED]"

    def fill_leaf(self, i, v):
        if i < 0 or i > 7:
            return False, "Index Error"
        if v == self.leaves[i]:
            self.student_leaves[i] = v
            return True, "Leaf Validated."
        return False, "Incorrect Hash."

    def smart_combine(self, l, r):
        c = self.sha256_hash(l + r)
        for i in range(4):
            if c == self.level1[i]:
                self.student_level1[i] = c
                return True, f"Created L1 Node {i}"
        for i in range(2):
            if c == self.level2[i]:
                self.student_level2[i] = c
                return True, f"Created L2 Node {i}"
        if c == self.root:
            self.student_root = c
            return True, "ROOT CALCULATED!"
        return False, f"Hash {c[:6]}... matches no empty slots."

    def _symmetric_encrypt(self, plaintext, key):
        nonce = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key), modes.CTR(nonce), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return base64.b64encode(nonce + ciphertext).decode()

    def _symmetric_decrypt(self, ciphertext_b64, key):
        try:
            data = base64.b64decode(ciphertext_b64)
            nonce, ciphertext = data[:16], data[16:]
            cipher = Cipher(
                algorithms.AES(key), modes.CTR(nonce), backend=default_backend()
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode()
        except:
            return "[DECRYPTION FAILED]"

    def _asym_encrypt(self, plaintext, public_key):
        ciphertext = public_key.encrypt(
            plaintext.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode()

    def _sign(self, message, private_key):
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def _verify(self, message, signature_b64, public_key):
        try:
            signature = base64.b64decode(signature_b64)
            public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except:
            return False

    # ==========================================
    # SCENARIO 1: S1 PII LEAK
    # ==========================================
    def s1_view_record(self):
        return f"{self.s1_record_text}\n\nSIGNATURE (Base64): {self.s1_record_signature[:60]}..."

    def s1_verify_signature(self):
        is_valid = self._verify(
            self.s1_record_text, self.s1_record_signature, self.s1_public_key
        )
        if is_valid:
            return "[VALID] SIGNATURE VALID: This record was authentically signed by the S1 Officer.\n\nCRITICAL FAILURE: The signature proves WHO created it, but the SSN is still in PLAINTEXT! Signatures do NOT provide confidentiality."
        return "[INVALID] SIGNATURE INVALID"

    def s1_encrypt_record(self, method):
        if method == "symmetric":
            return "[ERROR] POLICY VIOLATION: HQ policy mandates the use of Public/Private keys (Asymmetric) for SSN data to prevent the massive operational overhead of securely distributing Symmetric keys for every single record request."
        elif method == "hybrid":
            return "[ERROR] UNNECESSARY COMPLEXITY: While technically secure, deploying a full Hybrid Architecture (encrypting the data symmetrically, then encrypting the key asymmetrically) to protect a tiny 80-byte text record is extreme overkill. Keep it simple."
        elif method == "asymmetric":
            encrypted = self._asym_encrypt(self.s1_record_text, self.s1_public_key)
            self.scenario_state["s1_record_secured"] = True
            self.scenario_state["s1_completed"] = True
            return f"[SUCCESS] ASYMMETRIC ENCRYPTION APPLIED.\n\nCiphertext: {encrypted[:60]}...\n\nBecause the data payload is so small, pure Asymmetric (RSA) encryption handles it perfectly while fully satisfying the HQ Public Key policy."
        return "Invalid method. Use 'symmetric', 'asymmetric', or 'hybrid'."

    # ==========================================
    # SCENARIO 2: EMBASSY COLLABORATOR
    # ==========================================
    def s2_view_intercept(self):
        return f"ENCRYPTED COMM (AES-256):\n{self.encrypted_message[:80]}...\n\nThe local national collaborator has the encrypted file, but they need the decryption key to read it!"

    def s2_send_key_plaintext(self):
        return "[ERROR] SECURITY BREACH! You sent the symmetric key in plaintext over an unclassified channel. Adversaries have intercepted it and decrypted the extraction coordinates."

    def s2_send_key_encrypted(self):
        encrypted_key = self._asym_encrypt(
            self.symmetric_key.hex(), self.collab_public_key
        )
        self.scenario_state["s2_key_sent_securely"] = True
        self.scenario_state["s2_completed"] = True
        return f"[SUCCESS] KEY SENT SECURELY!\n\nEncrypted Key: {encrypted_key[:60]}...\n\nThe collaborator uses their private key to decrypt this, recovers the symmetric key, and decrypts the extraction coordinates."

    # ==========================================
    # SCENARIO 3: AMBASSADOR FORGERY
    # ==========================================
    def s3_view_cables(self):
        output = "THREE CABLES RECEIVED:\n\n"
        for c_id, c_data in self.signed_cables.items():
            output += f"[{c_id}] {c_data['text'][:80]}...\n\n"
        return output

    def s3_verify_cable(self, cable_id, pub_key_ref):
        if pub_key_ref != "amb_public_key":
            return f"[ERROR]: You must explicitly provide the known public key to verify against (e.g., 'verify_cable {cable_id} amb_public_key'). Otherwise, you might be validating against the imposter's key!"

        c_id = cable_id.upper()
        if c_id not in self.signed_cables:
            return "Invalid cable ID. Use A, B, or C."

        c_data = self.signed_cables[c_id]
        is_valid = self._verify(c_data["text"], c_data["signature"], self.amb_public)

        if is_valid:
            self.scenario_state["s3_ambassador_verified"] = True
            self.scenario_state["s3_completed"] = True
            return f"[VALID] CABLE {c_id}: SIGNATURE VALID\n\n{c_data['text']}\n\nThis was cryptographically signed by the Ambassador's true private key."
        else:
            return f"[INVALID] CABLE {c_id}: SIGNATURE INVALID\n\n{c_data['text']}\n\nThis was NOT signed by the Ambassador. It is enemy disinformation!"

    # ==========================================
    # SCENARIO 4: THE 1GB ISR VIDEO
    # ==========================================
    def s4_send_file(self, method):
        if method == "symmetric":
            return "[INCOMPLETE]: The 1GB ISR video was successfully encrypted using Symmetric cryptography. It was fast enough to handle the massive file, but now you have a raw AES key. How will you securely transmit this key to headquarters over an unclassified channel? You need to combine methods."

        elif method == "asymmetric":
            return "[ERROR]: The 1GB ISR video is too massive! Asymmetric encryption (RSA) operates at a few kilobytes per second and is mathematically limited to payloads smaller than its key size. Encrypting 1GB with raw RSA would take hours and crash the system."

        elif method == "hybrid":
            self.scenario_state["s4_video_sent"] = True
            self.scenario_state["s4_completed"] = True
            return "[SUCCESS]: 1GB ISR video secured using HYBRID CRYPTOGRAPHY!\n\n1. Symmetrically encrypted the 1GB video (Fast, handles bulk data).\n2. Asymmetrically encrypted the symmetric key with the recipient's Public Key.\n\nThis proves why modern secure communications (like TLS/HTTPS) must use Hybrid architecture for large transfers."

        return "Invalid parameters. Try 'send_file symmetric', 'send_file asymmetric', or 'send_file hybrid'."
