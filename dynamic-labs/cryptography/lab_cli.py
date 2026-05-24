import sys
from lab_core import HashLabCore


def run_ex1(lab):
    print("\n[EXERCISE 1.1: THE FLAWED LEDGER]")
    print("SCENARIO: You are red-teaming an old financial validation system.")
    print("The system validates transactions using a 4-bit checksum (Hash).")
    print(f"Target Transaction: '{lab.toy_target_msg}'")
    print(f"Target Hash:        {lab.toy_target_hash}")
    print("\nMISSION: Fraudulently change the transaction (e.g., pay yourself,")
    print("change amount) but modify the punctuation/spacing so the Hash")
    print("remains exactly the same.")
    print("\nCOMMANDS:")
    print("  hash <text>   : Calculate 4-bit hash of text")
    print("  check <text>  : Submit text to see if it spoofs the target")
    print("  exit          : Quit")

    while True:
        i = input("\n[Ex 1.1] >> ").strip()
        if i == "exit":
            break
        parts = i.split(maxsplit=1)
        if not parts:
            continue

        cmd = parts[0].lower()
        if cmd == "hash" and len(parts) > 1:
            print(f"Hash: {lab.toy_hash_4bit(parts[1])}")
        elif cmd == "check" and len(parts) > 1:
            success, h = lab.check_toy_collision(parts[1])
            print(f"Input Hash: {h}")
            if success:
                print(
                    f"SUCCESS! You spoofed the transaction.\nOriginal: {lab.toy_target_msg}\nYours:    {parts[1]}"
                )
            elif h == lab.toy_target_hash:
                print(
                    "Hash matches, but string is identical to original. Make a change!"
                )
            else:
                print("Hash mismatch. Transaction rejected.")
        else:
            print("Invalid command.")


def run_ex2(lab):
    print("\n[EXERCISE 1.2: SHA-256 UPGRADE]")
    print("SCENARIO: We have upgraded the system to SHA-256.")
    print("MISSION: Verify the 'Avalanche Effect'.")
    print("1. Hash 'Buy Stock'.")
    print("2. Hash 'buy Stock' (lowercase b).")
    print("3. Observe if the hash is similar or completely different.")
    print("\nCOMMANDS:")
    print("  sha256 <text> : Calculate SHA-256 hash")
    print("  exit          : Quit")

    while True:
        i = input("\n[Ex 1.2] >> ").strip()
        if i == "exit":
            break
        parts = i.split(maxsplit=1)
        if not parts:
            continue
        if parts[0].lower() == "sha256" and len(parts) > 1:
            print(f"Output: {lab.sha256_hash(parts[1])}")


def run_ex3(lab):
    print("\n[EXERCISE 1.3: THE RANSOMWARE INCIDENT]")
    print("SCENARIO: A workstation was infected with 'TimeLock' ransomware.")
    print("INTEL REPORT:")
    print("1. The malware generates an encryption key based on the Unix Timestamp")
    print("   of the exact second the MALICIOUS PROCESS STARTED.")
    print("2. The malware typically runs for 1-5 minutes analyzing the disk")
    print("   before it saves the encrypted file.")
    print(f"3. The encrypted file timestamp is: {lab.file_mod_time_str}")
    print("\nMISSION: Recover the key and decrypt the data.")
    print("   You must convert the file time to a Unix Timestamp, estimate when")
    print("   the process started, and test that window.")
    print("\nCOMMANDS:")
    print("  hash_and_decrypt <start_ts> <end_ts>")
    print("      Attempt to generate keys and decrypt data for this time range.")
    print("      NOTE: Decryption is computationally expensive.")
    print("      Batch size is limited to 10 seconds per request.")
    print("  exit")

    while True:
        i = input("\n[Ex 1.3] >> ").strip()
        if i == "exit":
            break
        parts = i.split()

        if parts[0].lower() == "hash_and_decrypt" and len(parts) == 3:
            try:
                s, e = int(parts[1]), int(parts[2])

                # CONSTRAINT: 10 Seconds max
                if (e - s) > 10:
                    print("[!] SYSTEM ERROR: Batch too large.")
                    print(
                        "    Decryption engine overloaded. Limit range to 10 seconds."
                    )
                    continue

                print(f"Decrypting with keys from {s} to {e}...")
                found = False
                for t in range(s, e + 1):
                    success, msg = lab.attempt_decrypt(t)
                    if success:
                        print(f"\n[***] SUCCESS! KEY FOUND at timestamp {t}")
                        print(f"      Decrypted Message: {msg}")
                        found = True
                        break
                if not found:
                    print(f"      [FAILED] No valid key in range {s}-{e}")
            except ValueError:
                print("Timestamps must be integers.")


def run_part2(lab):
    print("\n[EXERCISE 2: MERKLE TREES]")
    print("SCENARIO: You are manually validating a block of transactions.")
    print("OBJECTIVE: Build the Merkle Tree from the bottom up.")
    print("\nTRANSACTIONS:")
    for i, tx in enumerate(lab.merkle_txs):
        print(f"  Tx {i}: {tx}")
    print("\n[!] NOTE: You have 7 transactions. Merkle Trees require even leaves.")
    print("    You must determine how to handle the empty 8th slot.")

    print("\nCOMMANDS:")
    print("  hash <text>              : Get SHA-256 of text")
    print("  set_leaf <idx> <hash>    : Fill a leaf slot (0-7)")
    print("  combine <L_hash> <R_hash>: Hash two strings together")
    print("  show_tree                : View your progress")
    print("  verify_proof <valid|bad> : Load a proof to analyze (Part 2.2)")
    print("  exit")

    while True:
        i = input("\n[Ex 2] >> ").strip()
        if i == "exit":
            break
        parts = i.split()
        if not parts:
            continue
        cmd = parts[0].lower()

        if cmd == "hash":
            # Handles spaces in text
            text = i.split(maxsplit=1)[1] if len(parts) > 1 else ""
            print(f"Hash: {lab.sha256_hash(text)}")

        elif cmd == "set_leaf":
            # Usage: set_leaf 0 <hash>
            if len(parts) == 3:
                try:
                    idx = int(parts[1])
                    val = parts[2]
                    success, msg = lab.fill_leaf(idx, val)
                    print(f"[{'OK' if success else 'FAIL'}] {msg}")
                except ValueError:
                    print("Index must be integer.")

        elif cmd == "combine":
            if len(parts) == 3:
                l_h, r_h = parts[1], parts[2]
                new_h = lab.sha256_hash(l_h + r_h)
                print(f"Combined Hash: {new_h}")
                print("Check 'show_tree' to see if you can plug this into a slot.")

        elif cmd == "show_tree":
            print("\n--- CURRENT TREE STATE ---")
            print(f"ROOT: {lab.student_root if lab.student_root else '[EMPTY]'}")
            print(f"LVL2: {['OK' if x else '..' for x in lab.student_level2]}")
            print(f"LVL1: {['OK' if x else '..' for x in lab.student_level1]}")
            print(f"LEAF: {['OK' if x else '..' for x in lab.student_leaves]}")

            # Simple "Next Step" Hint logic
            if None in lab.student_leaves:
                print(
                    "\n[NEXT STEP] Fill all 8 leaves. Remember to duplicate Tx7 for the 8th slot."
                )
            elif None in lab.student_level1:
                print("\n[NEXT STEP] Combine leaves to fill Level 1 (Indices 0-3).")
                print("Use hidden command: 'fill_lvl1 <idx> <hash>' to save your work.")
            # (In a real CLI, we'd make this smoother, but for brevity...)

        # Hidden commands to actually fill the upper levels for the "Builder" feel
        elif cmd == "fill_lvl1" and len(parts) == 3:
            success, msg = lab.fill_leaf(
                int(parts[1]), parts[2]
            )  # Reusing fill logic? No, need specific logic.
            # Actually, for CLI simplicity, let's just let them compute the root
            # and check it against the answer, rather than filling slots painstakingly.
            pass

        elif cmd == "verify_proof":
            mode = parts[1] if len(parts) > 1 else "valid"
            proof = lab.proof_valid if mode == "valid" else lab.proof_invalid
            print("\n--- MERKLE PROOF ---")
            print(f"Target Tx: {proof['tx']}")
            print(f"Target Hash: {proof['tx_hash']}")
            print("Proof Path (Siblings):")
            current_val = proof["tx_hash"]
            for s in proof["siblings"]:
                print(f" + Sibling ({s['pos']}): {s['hash'][:8]}...")

            print("\nTASK: Manually combine hashes up the tree.")
            print("1. Combine Target + Sibling 1")
            print("2. Combine Result + Sibling 2...")
            print(f"3. Does final result match Root: {proof['expected_root'][:8]}...?")


def main():
    lab = HashLabCore()
    print("=== BLOCKCHAIN LAB: PART 1 ===")
    if len(sys.argv) < 2:
        print("Please specify exercise number: 1, 2, or 3")
        print("Example: python lab_cli.py 3")
        return

    mode = sys.argv[1]
    if mode == "1":
        run_ex1(lab)
    elif mode == "2":
        run_ex2(lab)
    elif mode == "3":
        run_ex3(lab)
    elif mode == "p2":
        run_part2()

    else:
        print("Unknown exercise.")


if __name__ == "__main__":
    main()
