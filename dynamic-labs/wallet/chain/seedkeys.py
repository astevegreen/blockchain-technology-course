"""Seed phrase to extended keys (BIP 39 and BIP 32), Python standard library only.

    python3 seedkeys.py "<phrase>" <path> [passphrase]

prints JSON: the master fingerprint, and the extended private and public keys at <path>
(e.g. m/84'/0'/0'). build-steps.sh hands these keys to bitcoind as descriptors; the wallet page
(gateway/static/wallet/) derives the same keys in the browser, and the tests compare the two.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys

P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
XPRV, XPUB = 0x0488ADE4, 0x0488B21E


def point_add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a[0] == b[0] and (a[1] + b[1]) % P == 0:
        return None
    if a == b:
        lam = 3 * a[0] * a[0] * pow(2 * a[1], -1, P) % P
    else:
        lam = (b[1] - a[1]) * pow(b[0] - a[0], -1, P) % P
    x = (lam * lam - a[0] - b[0]) % P
    return x, (lam * (a[0] - x) - a[1]) % P


def point_mul(k: int):
    result, addend = None, G
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def ser_p(k: int) -> bytes:
    x, y = point_mul(k)
    return bytes([2 + (y & 1)]) + x.to_bytes(32, "big")


def hash160(data: bytes) -> bytes:
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


def b58check(payload: bytes) -> str:
    data = payload + hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(data, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + out


def derive(phrase: str, path: str, passphrase: str = "") -> dict:
    seed = hashlib.pbkdf2_hmac("sha512", phrase.encode(), ("mnemonic" + passphrase).encode(), 2048)
    i = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    k, chain = int.from_bytes(i[:32], "big"), i[32:]
    master_fp = hash160(ser_p(k))[:4]
    depth, parent_fp, child = 0, b"\0" * 4, 0
    for step in [s for s in path.split("/")[1:] if s]:
        hardened = step.endswith(("'", "h"))
        child = int(step.rstrip("'h")) + (0x80000000 if hardened else 0)
        data = (b"\0" + k.to_bytes(32, "big")) if hardened else ser_p(k)
        i = hmac.new(chain, data + child.to_bytes(4, "big"), hashlib.sha512).digest()
        parent_fp = hash160(ser_p(k))[:4]
        k, chain, depth = (int.from_bytes(i[:32], "big") + k) % N, i[32:], depth + 1
    head = depth.to_bytes(1, "big") + parent_fp + child.to_bytes(4, "big") + chain
    return {
        "fingerprint": master_fp.hex(),
        "path": path,
        "xprv": b58check(XPRV.to_bytes(4, "big") + head + b"\0" + k.to_bytes(32, "big")),
        "xpub": b58check(XPUB.to_bytes(4, "big") + head + ser_p(k)),
    }


if __name__ == "__main__":
    print(json.dumps(derive(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")))
