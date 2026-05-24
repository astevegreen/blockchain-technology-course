#!/usr/bin/env python3
import hashlib
import struct
import binascii
import time
import subprocess
import json
import sys
import argparse
import os

"""
AI Disclosure: this script was fully vibed by Gemini 3 Pro
"""

# --- CONFIGURATION ---
RPC_WALLET_FLAG = "-rpcwallet=student"  
VERBOSE = False

# --- LOGGING ---
def log(msg, level="INFO"):
    if level == "DEBUG" and not VERBOSE: return
    print(f"[{level}] {msg}")

# --- RPC CALLER ---
def rpc(method, params=None):
    if params is None: params = []
    
    cmd_params = []
    for p in params:
        if isinstance(p, (dict, list)):
            cmd_params.append(json.dumps(p))
        else:
            cmd_params.append(str(p))
            
    base_cmd = ["bitcoin-cli"]
    cmd = base_cmd + [RPC_WALLET_FLAG, method] + cmd_params
    
    if VERBOSE: log(f"EXEC: {' '.join(cmd)}", "DEBUG")

    try:
        result_bytes = subprocess.check_output(cmd, stderr=subprocess.PIPE)
        result_str = result_bytes.decode('utf-8').strip()
        
        if VERBOSE and result_str and len(result_str) < 500:
            log(f"RESP: {result_str}", "DEBUG")

        if not result_str: return None 

        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            return result_str

    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8').strip()
        if "Wallet file not specified" in err_msg or "Method not found" in err_msg:
            global_cmd = base_cmd + [method] + cmd_params
            try:
                res_bytes = subprocess.check_output(global_cmd, stderr=subprocess.PIPE)
                return json.loads(res_bytes.decode('utf-8').strip())
            except Exception as e2:
                log(f"RPC FAILED: {err_msg}", "ERROR")
                raise e
        else:
            log(f"RPC FAILED: {err_msg}", "ERROR")
            raise e

# --- CRYPTO ---
def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def compact_to_target(bits):
    exponent = bits >> 24
    mantissa = bits & 0xffffff
    if exponent <= 3:
        target = mantissa >> (8 * (3 - exponent))
    else:
        target = mantissa << (8 * (exponent - 3))
    return target

def ser_compact_size(l):
    if l < 253: return struct.pack("B", l)
    elif l < 65536: return struct.pack("<BH", 253, l)
    elif l < 4294967296: return struct.pack("<BI", 254, l)
    else: return struct.pack("<BQ", 255, l)

def calculate_merkle_root(tx_hashes):
    if not tx_hashes: raise ValueError("No transactions")
    level = tx_hashes
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i+1] if i + 1 < len(level) else left
            next_level.append(sha256d(left + right))
        level = next_level
    return level[0]

def get_script_pubkey(address):
    try:
        info = rpc("validateaddress", [address])
        if info and "scriptPubKey" in info:
            return binascii.unhexlify(info["scriptPubKey"])
        info = rpc("getaddressinfo", [address])
        if info and "scriptPubKey" in info:
            return binascii.unhexlify(info["scriptPubKey"])
    except Exception:
        pass
    log("Could not resolve scriptPubKey. Is the address valid?", "ERROR")
    sys.exit(1)

# --- SCRIPT BUILDERS ---
def encode_script_num(n):
    if n == 0: return b'\x00'
    if 1 <= n <= 16: return struct.pack("B", 0x50 + n)
    data = bytearray()
    neg = n < 0
    abs_n = abs(n)
    while abs_n:
        data.append(abs_n & 0xff)
        abs_n >>= 8
    if data[-1] & 0x80:
        data.append(0x80 if neg else 0x00)
    elif neg:
        data[-1] |= 0x80
    return push_data(bytes(data))

def push_data(data):
    l = len(data)
    if l < 76: return struct.pack("B", l) + data
    elif l < 256: return b'\x4c' + struct.pack("B", l) + data
    elif l < 65536: return b'\x4d' + struct.pack("<H", l) + data
    else: return b'\x4e' + struct.pack("<I", l) + data

# --- PARSER UTILS ---
class BytesStream:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        
    def read(self, n):
        if self.pos + n > len(self.data): raise ValueError("Unexpected End of Stream")
        ret = self.data[self.pos:self.pos+n]
        self.pos += n
        return ret
        
    def peek(self, n):
        if self.pos + n > len(self.data): return b''
        return self.data[self.pos:self.pos+n]
        
    def read_varint(self):
        prefix = self.read(1)
        val = prefix[0]
        if val < 0xfd:
            return prefix, val
        elif val == 0xfd:
            val_bytes = self.read(2)
            return prefix + val_bytes, struct.unpack("<H", val_bytes)[0]
        elif val == 0xfe:
            val_bytes = self.read(4)
            return prefix + val_bytes, struct.unpack("<I", val_bytes)[0]
        else:
            val_bytes = self.read(8)
            return prefix + val_bytes, struct.unpack("<Q", val_bytes)[0]

# --- TRANSACTION PARSING ---
def parse_tx(raw_hex, tx_index):
    """
    Returns a list of tuples: (data_bytes, label, description, indent_level)
    """
    stream = BytesStream(binascii.unhexlify(raw_hex))
    parts = []
    
    # Header Marker
    parts.append((b'', f"=== TX #{tx_index} ===", "", 0))
    
    # 1. Version
    v = stream.read(4)
    parts.append((v, "Version", "Tx Version", 0))
    
    # 2. Segwit Check
    is_segwit = False
    if stream.peek(1) == b'\x00':
        marker = stream.read(1)
        flag = stream.read(1)
        if flag == b'\x01':
            is_segwit = True
            parts.append((marker + flag, "Segwit", "Marker (00) Flag (01)", 0))
            
    # 3. Inputs
    count_bytes, count = stream.read_varint()
    parts.append((count_bytes, "InCount", f"{count} Inputs", 0))
    
    for i in range(count):
        parts.append((b'', f"Input #{i}", "", 1)) # Section Header
        
        prev_hash = stream.read(32)
        parts.append((prev_hash, "PrevHash", "Previous Tx Hash", 2))
        
        prev_idx = stream.read(4)
        idx_int = struct.unpack("<I", prev_idx)[0]
        parts.append((prev_idx, "PrevIdx", f"Index {idx_int}", 2))
        
        sl_bytes, sl = stream.read_varint()
        parts.append((sl_bytes, "ScriptLen", f"{sl} bytes", 2))
        
        if sl > 0:
            script = stream.read(sl)
            parts.append((script, "ScriptSig", "Signature Script", 2))
            
        seq = stream.read(4)
        parts.append((seq, "Sequence", "Tx Sequence", 2))
        
    # 4. Outputs
    out_count_bytes, out_count = stream.read_varint()
    parts.append((out_count_bytes, "OutCount", f"{out_count} Outputs", 0))
    
    for i in range(out_count):
        parts.append((b'', f"Output #{i}", "", 1)) # Section Header

        val = stream.read(8)
        val_int = struct.unpack("<Q", val)[0]
        parts.append((val, "Value", f"{val_int} Satoshis", 2))
        
        sl_bytes, sl = stream.read_varint()
        parts.append((sl_bytes, "ScriptLen", f"{sl} bytes", 2))
        
        if sl > 0:
            script = stream.read(sl)
            parts.append((script, "ScriptPub", "Pubkey Script", 2))
            
    # 5. Witness Data
    if is_segwit:
        for i in range(count): 
            parts.append((b'', f"Witness #{i}", f"Stack for Input {i}", 1))
            stack_count_bytes, stack_count = stream.read_varint()
            parts.append((stack_count_bytes, "Count", f"{stack_count} items", 2))
            
            for j in range(stack_count):
                item_len_bytes, item_len = stream.read_varint()
                parts.append((item_len_bytes, "ItemLen", f"{item_len} bytes", 2))
                
                if item_len > 0:
                    item = stream.read(item_len)
                    parts.append((item, "Data", "Witness Data", 2))
    
    # 6. Locktime
    lock = stream.read(4)
    parts.append((lock, "Locktime", "Block Height / Time", 0))
    
    return parts

# --- VISUALIZER ---
def print_block_breakdown(parts, title="SERIALIZED BLOCK STRUCTURE"):
    """
    Field-by-field layout.
    """
    print("\n" + "#"*60)
    print(f"  {title}")
    print("#"*60)
    
    for data, label, desc, indent in parts:
        
        # Handle Section Headers (empty data)
        if data == b'':
            prefix = "    " * indent
            print(f"\n{prefix}___ {label} ___")
            continue

        hex_str = binascii.hexlify(data).decode()
        prefix = "    " * indent
        
        # Layout:
        # [Indent] Label: Description
        # [Indent] Hex:   <Full Hex String>
        print(f"{prefix}{label}: {desc}")
        print(f"{prefix}Hex: {hex_str}")
                
    print("\n" + "#"*60 + "\n")

# --- MINING ---
def mine_block(target_address=None):
    print("⛏️  Initializing Miner...")

    # 1. Get Template
    try:
        template = rpc("getblocktemplate", [{"rules": ["segwit"]}])
    except Exception:
        log("Could not get block template.", "ERROR")
        sys.exit(1)

    height = template['height']
    prev_hash_hex = template['previousblockhash']
    prev_hash = binascii.unhexlify(prev_hash_hex)[::-1]
    bits = int(template['bits'], 16)
    cur_time = int(time.time())
    if cur_time <= template['mintime']: cur_time = template['mintime'] + 1

    # 2. Prepare Coinbase Output
    reward_val = template['coinbasevalue']
    if target_address:
        script_pubkey = get_script_pubkey(target_address)
    else:
        script_pubkey = b'\x01\x51' # OP_TRUE
    
    witness_commitment = None
    if 'default_witness_commitment' in template:
        witness_commitment = binascii.unhexlify(template['default_witness_commitment'])
    
    # 3. Build Coinbase Structure (Manual assembly for correctness)
    
    # Version
    cb_ver = struct.pack("<I", 1)
    
    # Marker/Flag (SegWit)
    cb_marker_flag = b''
    if witness_commitment:
        cb_marker_flag = b'\x00\x01'

    # Input
    cb_in_count = b'\x01'
    cb_prev_hash = b'\x00'*32
    cb_prev_idx = b'\xff\xff\xff\xff'
    
    height_script = encode_script_num(height)
    extra_nonce = b'Student Miner'
    script_sig = height_script + push_data(extra_nonce)
    cb_script_len = ser_compact_size(len(script_sig))
    cb_seq = b'\xff\xff\xff\xff'

    # Outputs
    out_count_int = 2 if witness_commitment else 1
    cb_out_count = ser_compact_size(out_count_int)

    # Output 1 (Reward)
    cb_val = struct.pack("<Q", reward_val)
    cb_pk_len = ser_compact_size(len(script_pubkey))
    
    # Output 2 (Witness Commitment)
    cb_wit_out = b''
    if witness_commitment:
        cb_wit_val = struct.pack("<Q", 0)
        cb_wit_len = ser_compact_size(len(witness_commitment))
        cb_wit_out = cb_wit_val + cb_wit_len + witness_commitment

    # Witness Data (SegWit)
    cb_witness = b''
    if witness_commitment:
        cb_witness = b'\x01\x20' + (b'\x00' * 32)

    cb_lock = b'\x00\x00\x00\x00'

    # Assemble Bytes
    coinbase_bytes = (
        cb_ver + cb_marker_flag + cb_in_count + cb_prev_hash + cb_prev_idx + 
        cb_script_len + script_sig + cb_seq + cb_out_count + 
        cb_val + cb_pk_len + script_pubkey + cb_wit_out + 
        cb_witness + cb_lock
    )

    # Calculate Coinbase TXID (Legacy)
    legacy_tx = (
        cb_ver + cb_in_count + cb_prev_hash + cb_prev_idx + 
        cb_script_len + script_sig + cb_seq + cb_out_count + 
        cb_val + cb_pk_len + script_pubkey + cb_wit_out + cb_lock
    )
    coinbase_txid = sha256d(legacy_tx)

    # 4. Merkle Root
    tx_hashes = [coinbase_txid]
    transactions = template.get('transactions', [])
    for tx in transactions:
        tx_id_hex = tx.get('txid', tx['hash'])
        tx_hashes.append(binascii.unhexlify(tx_id_hex)[::-1])
        
    merkle_root = calculate_merkle_root(tx_hashes)

    print(f"   ├── Height: {height}")
    print(f"   ├── Txs: {len(transactions)}")
    print(f"   ├── SegWit: {'Yes' if witness_commitment else 'No'}")
    print(f"   └── Merkle: {binascii.hexlify(merkle_root[::-1]).decode()}")

    # 5. Build Header
    version_bytes = struct.pack("<I", 0x20000000)
    time_bytes = struct.pack("<I", cur_time)
    bits_bytes = struct.pack("<I", bits)

    # 6. Mine
    target = compact_to_target(bits)
    nonce = 0
    print("\n🔨 STARTING HASHING...")
    start_t = time.time()
    
    found_header = None
    
    while True:
        nonce_bytes = struct.pack("<I", nonce)
        header = version_bytes + prev_hash + merkle_root + time_bytes + bits_bytes + nonce_bytes
        block_hash = sha256d(header)
        
        if int.from_bytes(block_hash, 'little') <= target:
            print(f"\n🎉 SUCCESS! Nonce: {nonce} ({round(time.time()-start_t, 2)}s)")
            found_header = header
            break
        nonce += 1
        if nonce % 200000 == 0:
            sys.stdout.write(f"\r   Checking: {nonce}...")
            sys.stdout.flush()

    # 7. Construct BLOCK STRUCTURE (High Level Breakdown)
    block_parts = []
    
    # Header Section
    block_parts.append((b'', "=== BLOCK HEADER ===", "", 0))
    block_parts.append((found_header[:4], "Version", "Block Version", 0))
    block_parts.append((found_header[4:36], "PrevHash", "Hash of prev block", 0))
    block_parts.append((found_header[36:68], "MerkleRoot", "Root of all Txs", 0))
    block_parts.append((found_header[68:72], "Time", f"Unix ({cur_time})", 0))
    block_parts.append((found_header[72:76], "Bits", "Target Compact", 0))
    block_parts.append((found_header[76:80], "Nonce", f"Winning ({nonce})", 0))

    # Tx Count
    tx_count_bytes = ser_compact_size(len(tx_hashes))
    block_parts.append((tx_count_bytes, "TxCount", f"{len(tx_hashes)} Txs", 0))
    
    # Coinbase Parse (Recycle bytes via parse_tx for details)
    cb_parsed = parse_tx(binascii.hexlify(coinbase_bytes), 0)
    cb_parsed[0] = (b'', "=== COINBASE (Tx #0) ===", "Mining Reward", 0) 
    block_parts.extend(cb_parsed)
    
    # Other Txs (Raw Blobs for Normal Mode)
    full_block = found_header + tx_count_bytes + coinbase_bytes
    
    for i, tx in enumerate(transactions):
        tx_data = binascii.unhexlify(tx['data'])
        tx_id = tx.get('txid', tx['hash'])
        block_parts.append((b'', f"=== TX #{i+1} ===", "", 0))
        block_parts.append((tx_data, "Tx Data", f"ID: {tx_id[:8]}...", 0))
        full_block += tx_data

    # 8. Print Block Structure (Always)
    print_block_breakdown(block_parts, "SERIALIZED BLOCK STRUCTURE")

    # 9. Print Transaction Deep Dive (Only Verbose)
    if VERBOSE and transactions:
        tx_dive_parts = []
        for i, tx in enumerate(transactions):
            tx_dive_parts.extend(parse_tx(tx['data'], i+1))
        
        print_block_breakdown(tx_dive_parts, "TRANSACTION DEEP DIVE")

    # 10. Submit
    print("📡 Submitting block...")
    hex_block = binascii.hexlify(full_block).decode()
    res = rpc("submitblock", [hex_block])
    
    if res is None:
        print("✅ Block Accepted!")
    elif res == "duplicate":
        print("⚠️  Block Duplicate.")
    else:
        print(f"❌ Rejected: {res}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="Wallet address to mine to")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging & Block Breakdown")
    args = parser.parse_args()
    
    VERBOSE = args.verbose
    
    try:
        mine_block(args.address)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")