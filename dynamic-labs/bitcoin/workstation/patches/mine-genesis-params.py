import hashlib
import struct
import binascii
import time

# --- CONFIGURATION (MUST MATCH C++ EXACTLY) ---
pszTimestamp = "ClassNet 2026: Students mine the first block"
pszTimestamp = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
# The standard pubkey used in Bitcoin Core (legacy)
pubkey_hex = "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
nVersion = 1
nTime = int(time.time())
nBits = 0x207fffff  # The "Easy" Limit
initial_reward = 50 * 100000000

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
    if l < 253:
        return struct.pack("B", l)
    elif l < 65536:
        return struct.pack("<BH", 253, l)
    elif l < 4294967296:
        return struct.pack("<BI", 254, l)
    else:
        return struct.pack("<BQ", 255, l)

def create_merkle_root():
    # 1. Input Transaction (Vin)
    # PrevHash (32 bytes 0) + PrevIndex (0xffffffff)
    vin_prev_hash = b'\x00' * 32
    vin_prev_index = struct.pack("<I", 0xffffffff)
    
    # ScriptSig: nBits + CScriptNum(4) + timestamp
    # serialization of CScriptNum(4) depends on version, but for genesis it's usually:
    # 0x01 (len) 0x04 (value) -> THIS IS CRITICAL. 
    # Standard bitcoin uses "04ffff001d" + "0104" + ...
    # Our nBits is 0x207fffff -> 04 ffffff20 (little endian)
    
    # Push nBits (4 bytes)
    # Since 0x207fffff takes 4 bytes, it is pushed as: [04] [ff ff 7f 20]
    # Note: Bitcoin serializes integer nBits little-endian.
    nbits_bytes = struct.pack("<I", nBits) 
    script_p1 = b'\x04' + nbits_bytes
    
    # Push 4 (CScriptNum(4))
    # In the original genesis, this resulted in byte \x04 being pushed with len 1.
    script_p2 = b'\x01\x04'
    
    # Push Timestamp
    ts_bytes = pszTimestamp.encode('ascii')
    script_p3 = ser_compact_size(len(ts_bytes)) + ts_bytes
    
    script_sig_inner = script_p1 + script_p2 + script_p3
    script_sig = ser_compact_size(len(script_sig_inner)) + script_sig_inner
    
    vin_seq = b'\xff\xff\xff\xff'
    vin = vin_prev_hash + vin_prev_index + script_sig + vin_seq

    # 2. Output Transaction (Vout)
    vout_value = struct.pack("<Q", initial_reward)
    
    # ScriptPubKey: PubKey + OP_CHECKSIG (0xac)
    pk_bytes = binascii.unhexlify(pubkey_hex)
    script_pubkey_inner = ser_compact_size(len(pk_bytes)) + pk_bytes + b'\xac'
    script_pubkey = ser_compact_size(len(script_pubkey_inner)) + script_pubkey_inner
    
    vout = vout_value + script_pubkey

    # 3. Full Transaction
    # Version(1) + VinCount(1) + Vin + VoutCount(1) + Vout + LockTime(0)
    tx = struct.pack("<I", 1) + b'\x01' + vin + b'\x01' + vout + b'\x00\x00\x00\x00'
    
    # Merkle root is just sha256d of the single coinbase tx
    return sha256d(tx)

def mine():
    print(f"preparing to mine...")
    print(f"Timestamp: \"{pszTimestamp}\" ({nTime})")
    print(f"nBits: {nBits:#x}")

    merkle_root = create_merkle_root()
    merkle_root_hex = binascii.hexlify(merkle_root[::-1]).decode()
    print(f"Calculated Merkle Root: {merkle_root_hex}")
    
    target = compact_to_target(nBits)
    
    nonce = 0
    # Header: Version(4) + Prev(32) + Merkle(32) + Time(4) + Bits(4) + Nonce(4)
    # Prefill the constant parts
    header_prefix = struct.pack("<I", nVersion) + (b'\x00' * 32) + merkle_root + struct.pack("<I", nTime) + struct.pack("<I", nBits)
    
    print("Mining...")
    start = time.time()
    
    while True:
        header = header_prefix + struct.pack("<I", nonce)
        block_hash = sha256d(header)
        
        # Compare as integer (little endian for PoW check)
        hash_int = int.from_bytes(block_hash, 'little')
        
        if hash_int <= target:
            hash_hex = binascii.hexlify(block_hash[::-1]).decode()
            print(f"\n--- SUCCESS ---")
            print(f"Nonce:   {nonce}")
            print(f"Time:    {nTime}")
            print(f"Bits:    {nBits:#x}")
            print(f"Hash:    {hash_hex}")
            print(f"Merkle:  {merkle_root_hex}")
            return nonce, nTime, hash_hex, merkle_root_hex
            
        nonce += 1
        if nonce % 1000000 == 0:
            print(f"Checked {nonce} nonces...")

if __name__ == "__main__":
    mine()
