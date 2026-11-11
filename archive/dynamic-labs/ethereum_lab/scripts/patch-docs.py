#!/usr/bin/env python3
"""Patch MANUAL.md and ARCHITECTURE.md with new content."""
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# MANUAL.md
manual_path = os.path.join(root, "docs", "MANUAL.md")
with open(manual_path, "r", encoding="utf-8") as f:
    manual = f.read()

# Use curly quotes (U+201C, U+201D) to match file
manual = manual.replace(
    "3. Wait a few seconds. You should see a message like **\u201cReceived 5 ETH from faucet!\u201d** and your balance will increase.",
    "3. **Or copy your address:** Use **📋 Copy** to copy your address and share it with your instructor. They can paste it in the \"Fund by address\" section.",
)
manual = manual.replace(
    "If you see an error, check that the connection is OK and that the instructor\u2019s node (and faucet) is running. You can click **Get 5 ETH** again if the faucet allows it.",
    "If you see an error, check that the connection is OK and that the instructor\u2019s node is running.",
)
# Troubleshooting table (curly apostrophe in Instructor's)
manual = manual.replace(
    "| **Get 5 ETH does nothing / error** | Instructor\u2019s node and faucet must be running; ask them to check. |",
    "| **Request funds / Get 5 ETH does nothing** | Instructor\u2019s node must be running; ask them to check. Use **Request funds** to notify them. |",
)

with open(manual_path, "w", encoding="utf-8") as f:
    f.write(manual)
print("Patched MANUAL.md")

# ARCHITECTURE.md
arch_path = os.path.join(root, "docs", "ARCHITECTURE.md")
with open(arch_path, "r", encoding="utf-8") as f:
    arch = f.read()

old_line = "- **Students** either open the instructor\u2019s frontend URL or run the frontend locally and point it at the instructor\u2019s RPC and contract address."
new_text = """- **Lab API** (port 3000): session check (instructor IP restriction), fund requests, wallet-creation tracking per IP. Only the instructor\u2019s IP can access `?mode=instructor`.
- **Students** either open the instructor\u2019s frontend URL or run the frontend locally and point it at the instructor\u2019s RPC and contract address. New students (by IP) must create a wallet first; they can click **Request funds** to notify the instructor."""

arch = arch.replace(old_line, new_text)
with open(arch_path, "w", encoding="utf-8") as f:
    f.write(arch)
print("Patched ARCHITECTURE.md")
