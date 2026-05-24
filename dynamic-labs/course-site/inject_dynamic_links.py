#!/usr/bin/env python3

from pathlib import Path


PLACEHOLDER = "<!-- DYNAMIC_RUNTIME_LINKS -->"

BLOCK = """## Dynamic Labs

These links are available in the packaged VM and cloud deployment paths where the shared router is running at the site root.

### Dynamic Lab Routes

* [Ethereum Lab](/labs/ethereum_lab/)
* [Bitcoin Lab Student Terminal](/labs/bitcoin/)
* [Bitcoin Mempool](/labs/bitcoin/mempool/)
* [Bitcoin Explorer](/labs/bitcoin/btc-explorer/)
* [Consensus Lab Student Terminal](/labs/consensus/)
* [Consensus Lab Instructor Terminal](/labs/consensus/instructor/)
* [Cryptography Lab](/labs/cryptography/)
* [P2P Trust Lab Student Terminal](/labs/p2p_trust/)
* [P2P Trust Lab Instructor Terminal](/labs/p2p_trust/instructor/)
* [Hyperledger Fabric Lab](/labs/hlf/claim)

### Exercises and Quiz

* [Byzantine Generals Exercise](/exercises/bgp/)
* [The Insider Exercise](/exercises/insider/)
* [Quiz Engine](/quiz/)
"""


def main() -> None:
    index_path = Path("/work/blockchain-course/index.qmd")
    source = index_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in source:
        raise SystemExit(f"Placeholder not found in {index_path}")
    index_path.write_text(source.replace(PLACEHOLDER, BLOCK), encoding="utf-8")


if __name__ == "__main__":
    main()
