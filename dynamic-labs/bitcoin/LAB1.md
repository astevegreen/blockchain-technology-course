### **Lab 1: Bitcoin Fundamentals (Standalone Regtest)**

**Objective:**
Master the core CLI commands of Bitcoin Core in a private, sandboxed environment. You will create a blockchain from scratch, manage multiple wallets to simulate a transaction between two people, and deeply inspect the **Block Headers** to understand how the "Puzzle" (Proof of Work) is constructed.

**⚠️ Important:**
Your lab environment is already running a "ClassNet" Bitcoin node in the background for use in later labs. To avoid conflicts, **you must use the specific flags provided below** for this part of the lab.


**Infrastructure Links:**

* **Terminal:** [https://blockchain-6dd63ebf.training-as-code.com/labs/bitcoin/](https://blockchain-6dd63ebf.training-as-code.com/labs/bitcoin/)

  Click the link to claim a station. You'll be redirected to your personal
  session URL (`/labs/bitcoin/c/<your-uuid>/`) — bookmark it so you can
  return to the same station. The wrapper page includes a panel bar with
  Mempool, Explorer, My Static, and Peers buttons; the Peers dropdown
  shows which other stations are online and lets you open their shared
  address page in a new tab.


### **Step 1: Start a Private Regtest Node**

We will start a *separate* instance of Bitcoin Core listening on unique ports.

1. Create a separate directory for this lab:
```bash
mkdir -p ~/.bitcoin-regtest

```


2. Start the daemon in **Regtest** mode:
```bash
bitcoind -regtest -daemon \
  -datadir=$HOME/.bitcoin-regtest \
  -rpcport=18443 \
  -port=18444 \
  -fallbackfee=0.0001 \
  -txindex=1

```


3. Create the **`btc-lab1`** alias. Always use this alias for Part 1 commands:
```bash
alias btc-lab1="bitcoin-cli -regtest -datadir=$HOME/.bitcoin-regtest -rpcport=18443"

```


4. Verify the alias works and the chain is empty:
```bash
btc-lab1 getblockchaininfo

```



#### **Step 2: The Genesis of a Chain**

1. **Create Two Wallets:**
We will simulate a transaction between you ("Student") and a counterparty ("Alice").
```bash
btc-lab1 createwallet "student"
btc-lab1 createwallet "alice"

```


2. **Generate Addresses:**
```bash
STUDENT_ADDR=$(btc-lab1 -rpcwallet=student getnewaddress)
ALICE_ADDR=$(btc-lab1 -rpcwallet=alice getnewaddress)

```


3. **Mine the First Blocks:**
Bitcoin coins are only spendable after they "mature" (100 blocks deep). We will mine 11 blocks to the Student wallet to unlock the reward from Block #1.
```bash
btc-lab1 generatetoaddress 11 $STUDENT_ADDR

```

Note: normally it takes 100 blocks before a coinbase matures, but in this classroom version of the network,
the source code has been modified to only require 10 blocks.


4. **Check Balance:**
```bash
btc-lab1 -rpcwallet=student getbalance

```


*Result: You should see 50.0 BTC.*

### **Step 3: Anatomy of the Blockchain (Deep Dive)**

Now we will dissect the data you just created. Bitcoin is not just a ledger of balances; it is a chain of headers linked by hash proofs.

1. **Retrieve Block #1:**
Get the hash of the first block you mined:
```bash
BLOCK_HASH=$(btc-lab1 getblockhash 1)
echo $BLOCK_HASH

```


2. **Inspect the Block Header:**
Run the following command to see the JSON representation of the block:
```bash
btc-lab1 getblock $BLOCK_HASH

```


**Analyze these specific fields:**
* **`previousblockhash`**: The link to the past. This points to the Genesis Block (Block 0).
* **`merkleroot`**: The fingerprint of every transaction in this block.
* **`bits`**: The **Difficulty Target**. This compact number tells the miner how hard the puzzle is.
* **`nonce`**: The counter the miner changed millions of times to solve the puzzle.


3. **De-mystifying the "Bits" (Python Exercise):**
The field `bits` looks like a random hex string (e.g., `207fffff`), but it is actually a scientific notation representing a number. Let's calculate the actual target using Python.
```bash
python3 -c '
import sys
bits = 0x207fffff
exponent = bits >> 24
coefficient = bits & 0xffffff
target = coefficient * 256**(exponent - 3)
print(f"Target: {target:x}")
'

```


*Observation: The hash of your block must be numerically smaller than this massive "Target" number.*

### **Step 4: Anatomy of a Transaction**

1. **Send a Transaction:**
Send 10 BTC to Alice.
```bash
TXID=$(btc-lab1 -rpcwallet=student sendtoaddress $ALICE_ADDR 10)
echo $TXID

```


2. **Confirm the Transaction:**
Transactions stay in the "mempool" until mined. Mine one block to confirm it.
```bash
btc-lab1 generatetoaddress 1 $STUDENT_ADDR

```


3. **Decode the Coinbase Transaction (The Source of Funds):**
Before looking at your transaction to Alice, look at the transaction that funded *you*. Get the transaction ID of the coinbase in Block 1:
```bash
# Get the TXID of the first tx in block 1
CB_TXID=$(btc-lab1 getblock $(btc-lab1 getblockhash 1) | jq -r '.tx[0]')
btc-lab1 getrawtransaction $CB_TXID true | less
```

Note: Use the up and down arrows to scroll through the output. press `q` to close this view. 


*Notice the `vin` (Input). It has no `txid`! It has a `coinbase` field instead. This is money created from thin air.*

4. **Decode Your Spending Transaction:**
Now decode the transaction you sent to Alice:
```bash
btc-lab1 getrawtransaction $TXID true | less

```


*Notice the `vin` here references the Coinbase transaction you just looked at. This is the Chain of Ownership.*

#### **Step 5: Python Deep Dive (The Structure of Data)**

We will now use Python to manually parse the raw hex strings. This reveals how Bitcoin actually serializes data "on the wire."


1. **Get Raw Hex:**
Store the raw hex of your transaction in a variable for the script to use.
```bash
export RAW_TX_HEX=$(btc-lab1 getrawtransaction $TXID false)
echo $RAW_TX_HEX

```


2. **Create the Decoder Script:**
Create and populate a python3 script named `decoder.py`:
```bash
cat << 'EOF' > decoder.py
import os
import sys
from bitcoin.core import CTransaction, b2lx
from bitcoin.core.serialize import BytesIO

# 1. Get hex from environment variable
hex_str = os.environ.get('RAW_TX_HEX')
if not hex_str:
    print("Error: Set RAW_TX_HEX environment variable first.")
    sys.exit(1)

# 2. Deserialize (Parse the raw bytes)
tx_bytes = bytes.fromhex(hex_str)
tx = CTransaction.stream_deserialize(BytesIO(tx_bytes))

# FIX: Use b2lx (Bytes -> Little-endian Hex) for display, not lx
print(f"\n=== Transaction {b2lx(tx.GetTxid())} ===")
print(f"Version:  {tx.nVersion}")
print(f"LockTime: {tx.nLockTime}")

print(f"\n--- {len(tx.vin)} INPUTS (Spending) ---")
for i, vin in enumerate(tx.vin):
    print(f"Input #{i}:")
    # FIX: Use b2lx for the previous transaction hash
    print(f"  Prev TxID: {b2lx(vin.prevout.hash)}")
    print(f"  Prev Index: {vin.prevout.n}")
    # The ScriptSig proves we own the previous output
    print(f"  ScriptSig Size: {len(vin.scriptSig)} bytes")

print(f"\n--- {len(tx.vout)} OUTPUTS (Creating) ---")
for i, vout in enumerate(tx.vout):
    # nValue is stored in Satoshis (1 BTC = 100,000,000 Sats)
    btc_value = vout.nValue / 100000000
    print(f"Output #{i}:")
    print(f"  Value: {btc_value:.8f} BTC ({vout.nValue} sats)")
    print(f"  ScriptPubKey Size: {len(vout.scriptPubKey)} bytes")
EOF

```

The script uses `bitcoin.core` to deserialize the hex and print the internal fields. 
Here it is with syntax highlighting:
```python
import os
import sys
from bitcoin.core import CTransaction, b2lx
from bitcoin.core.serialize import BytesIO

# 1. Get hex from environment variable
hex_str = os.environ.get('RAW_TX_HEX')
if not hex_str:
    print("Error: Set RAW_TX_HEX environment variable first.")
    sys.exit(1)

# 2. Deserialize (Parse the raw bytes)
tx_bytes = bytes.fromhex(hex_str)
tx = CTransaction.stream_deserialize(BytesIO(tx_bytes))

# FIX: Use b2lx (Bytes -> Little-endian Hex) for display, not lx
print(f"\n=== Transaction {b2lx(tx.GetTxid())} ===")
print(f"Version:  {tx.nVersion}")
print(f"LockTime: {tx.nLockTime}")

print(f"\n--- {len(tx.vin)} INPUTS (Spending) ---")
for i, vin in enumerate(tx.vin):
    print(f"Input #{i}:")
    # FIX: Use b2lx for the previous transaction hash
    print(f"  Prev TxID: {b2lx(vin.prevout.hash)}")
    print(f"  Prev Index: {vin.prevout.n}")
    # The ScriptSig proves we own the previous output
    print(f"  ScriptSig Size: {len(vin.scriptSig)} bytes")

print(f"\n--- {len(tx.vout)} OUTPUTS (Creating) ---")
for i, vout in enumerate(tx.vout):
    # nValue is stored in Satoshis (1 BTC = 100,000,000 Sats)
    btc_value = vout.nValue / 100000000
    print(f"Output #{i}:")
    print(f"  Value: {btc_value:.8f} BTC ({vout.nValue} sats)")
    print(f"  ScriptPubKey Size: {len(vout.scriptPubKey)} bytes")

```

Note: a "sat" is a satoshi, or the smallest unit of bitcoin and represents
one-hundred-millionth of one coin. 

5. **Run the Decoder:**
```bash

python3 decoder.py

```


### **Step 6: The Merkle Root Challenge**

Why is the Merkle Root so important? It ensures the integrity of every transaction in the block. It is embedded directly in the 80-byte **Block Header**. Because the Block Hash is derived by hashing this 80-byte header, changing a single byte of any transaction changes the Merkle Root, which completely changes the Block Hash and breaks the Proof of Work.

In this challenge, you will modify the block data directly on disk to see how Bitcoin Core reacts to corruption.

Before we get started, let's use this script to 
do a quick refresh on how a single change to a single byte
of data feeding into a hash can completely change the 
output.

```bash
python3 -c '
import hashlib
def dsha256(x): return hashlib.sha256(hashlib.sha256(x).digest()).digest()

# Two fake transactions (64 bytes each)
tx_a = b"A" * 64
tx_b = b"B" * 64
root_original = dsha256(dsha256(tx_a) + dsha256(tx_b)).hex()

# Modify ONE byte of Tx A
tx_a_modified = b"a" + b"A" * 63
root_modified = dsha256(dsha256(tx_a_modified) + dsha256(tx_b)).hex()

print(f"Original Root: {root_original}")
print(f"Modified Root: {root_modified}")
'

```

Now let's modify the hash on the chain itself!

#### **Part 1: Inspect the Most Recent Block**

First, let's find the most recent block and locate its Merkle Root.

1. Get the hash of the best (most recent) block:

```bash
BEST_BLOCK=$(btc-lab1 getbestblockhash)
echo $BEST_BLOCK

```

2. Inspect the block details, specifically looking for the `"merkleroot"`:

```bash
btc-lab1 getblock $BEST_BLOCK | jq '{hash: .hash, merkleroot: .merkleroot, previousblockhash: .previousblockhash}'

```

3. Save the Merkle root to a variable for the next step:

```bash
MERKLE_ROOT=$(btc-lab1 getblock $BEST_BLOCK | jq -r '.merkleroot')

```

#### **Part 2: Corrupt the Block on Disk**

Bitcoin stores block data in `.dat` files (e.g., `blk00000.dat`). Interestingly, **the block hash itself is never stored in this file**. Instead, Bitcoin reads the 80-byte header and calculates the hash on the fly.

Let's use Python to find this block's Merkle Root on disk, corrupt it, and see what happens.

1. Create a script called `corrupt_block.py`:

```bash
nano corrupt_block.py

```

2. Paste the following Python code:

```python
import sys
import os

merkle_hex = sys.argv[1]
# Bitcoin stores data in little-endian format, reverse byte order
merkle_bytes = bytes.fromhex(merkle_hex)[::-1]

blocks_dir = os.path.expanduser("~/.bitcoin-regtest/regtest/blocks")
file_path = os.path.join(blocks_dir, "blk00000.dat")
xor_path = os.path.join(blocks_dir, "xor.dat")
backup_path = file_path + ".bak"

# 1. Read the XOR obfuscation key
with open(xor_path, "rb") as f:
    xor_key = f.read()

def apply_xor(data, key):
    """Applies or removes the rolling XOR obfuscation used by Bitcoin Core"""
    res = bytearray(len(data))
    key_len = len(key)
    for i in range(len(data)):
        res[i] = data[i] ^ key[i % key_len]
    return res

# 2. Read the raw obfuscated data
with open(file_path, "rb") as f:
    raw_data = bytearray(f.read())

# Create a backup so we can restore it later
if not os.path.exists(backup_path):
    with open(backup_path, "wb") as f:
        f.write(raw_data)

# 3. De-obfuscate the data into memory
data = apply_xor(raw_data, xor_key)

# 4. Search and Corrupt
idx = data.find(merkle_bytes)
if idx != -1:
    print(f"[*] Found Merkle Root at offset {idx} (De-obfuscated)")
    
    # Corrupt the Merkle Root
    corrupted_merkle = b'\xaa' * 32
    data[idx:idx+32] = corrupted_merkle
    
    # 5. Re-obfuscate the data and write to disk
    obfuscated_data = apply_xor(data, xor_key)
    with open(file_path, "wb") as f:
        f.write(obfuscated_data)
        
    print("[*] Merkle Root corrupted successfully! The block header is now altered.")
else:
    print("[!] Could not find the Merkle Root in the block file.")

```

3. Run the script, passing in the Merkle root:

```bash
python3 corrupt_block.py $MERKLE_ROOT

```

#### **Part 3: Validate the Chain and Observe the Error**

Now that the block file is corrupted on disk, let's ask Bitcoin Core to verify the integrity of our local blockchain.

1. Run the `verifychain` command (Check level `4` means thoroughly check all blocks, and we check the last `10` blocks):

```bash
btc-lab1 verifychain 4 10

```

*You should see this return `false`! Bitcoin Core has detected the corruption.*

2. Let's look at **why** it failed by inspecting the Bitcoin daemon's internal logs:

```bash
tail -n 20 ~/.bitcoin-regtest/regtest/debug.log

```

*Notice the errors? You'll likely see `hash mismatch` or `proof of work failed`. Because we changed the Merkle Root, the 80-byte header changed. When Bitcoin hashed the new header, the resulting Block Hash no longer matched the hash saved in the LevelDB block index, nor did it meet the network's Proof of Work difficulty (it lost its leading zeros).*

#### **Part 4: Compute the New Hash and Fix the Block**

To fix the block, we can't just "update the hash on disk" because the hash isn't stored there. We have to repair the underlying 80-byte header by restoring the valid Merkle Root. This recalculates the valid hash automatically.

1. Create a script called `fix_block.py`:

```bash
nano fix_block.py

```

2. Paste the following Python code:

```python
import os
import hashlib

def dsha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

blocks_dir = os.path.expanduser("~/.bitcoin-regtest/regtest/blocks")
file_path = os.path.join(blocks_dir, "blk00000.dat")
xor_path = os.path.join(blocks_dir, "xor.dat")
backup_path = file_path + ".bak"

with open(xor_path, "rb") as f:
    xor_key = f.read()

def apply_xor(data, key):
    res = bytearray(len(data))
    key_len = len(key)
    for i in range(len(data)):
        res[i] = data[i] ^ key[i % key_len]
    return res

# 1. Read the files
with open(file_path, "rb") as f:
    corrupted_data = apply_xor(f.read(), xor_key)

with open(backup_path, "rb") as f:
    pristine_data = apply_xor(f.read(), xor_key)

# Locate the corrupted segment (the 0xAA bytes we injected)
idx = corrupted_data.find(b'\xaa' * 32)

if idx != -1:
    # Extract the 80-byte header (Merkle root is 36 bytes into the 80 byte header)
    header_start = idx - 36
    corrupted_header = corrupted_data[header_start:header_start+80]
    
    invalid_hash = dsha256(corrupted_header)[::-1].hex()
    print(f"[*] The Block Hash of the CORRUPTED header is: {invalid_hash}")
    print(f"    (Notice it has no leading zeros! The Proof of Work is completely broken.)\n")

    # 3. Restore the correct Merkle Root from the pristine backup
    print("[*] Restoring the correct Merkle Root...")
    corrupted_data[idx:idx+32] = pristine_data[idx:idx+32]
    
    # Verify the restored hash
    restored_header = corrupted_data[header_start:header_start+80]
    valid_hash = dsha256(restored_header)[::-1].hex()
    print(f"[*] The Block Hash of the FIXED header is:     {valid_hash}")
    
    # 4. Re-obfuscate and Write
    fixed_obfuscated_data = apply_xor(corrupted_data, xor_key)
    with open(file_path, "wb") as f:
        f.write(fixed_obfuscated_data)
        
    print("\n[*] Block data successfully obfuscated and updated on disk.")
else:
    print("[!] Corrupted data not found. Has it already been fixed?")

```

3. Run the script to calculate the hashes and repair the block file:

```bash
python3 fix_block.py

```

4. Finally, validate the chain again using the Bitcoin CLI:

```bash
btc-lab1 verifychain 4 10

```

*It should now return `true`! You have successfully manipulated the raw storage of a Bitcoin node, observed the cryptographic chain of custody failing, and restored the mathematical properties of the block.*


### **Step 7: Clean Up**

Stop the private node:

```bash
btc-lab1 stop

```

