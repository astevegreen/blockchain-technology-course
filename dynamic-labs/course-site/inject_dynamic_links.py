#!/usr/bin/env python3

from pathlib import Path


PLACEHOLDER = "<!-- DYNAMIC_RUNTIME_LINKS -->"

BLOCK = """## Dynamic Labs

Use this section when the packaged VM or cloud lab stack is running.

### Student Starting Point

* [Student lab and quiz login](/quiz/student/) - start here to get or enter a student identifier and access assigned dynamic work.

### Student Lab Workspaces

Use these links after the instructor tells the class which lab is active.

* [Social Trust Lab: The Insider](/exercises/insider/)
* [Byzantine Generals Lab](/exercises/bgp/)
* [Explorer Lab](/labs/explorer/)
* [Cryptography Lab](/labs/cryptography/)
* [P2P Trust Lab](/labs/p2p_trust/)
* [Consensus Lab](/labs/consensus/)
* [Bitcoin Lab](/labs/bitcoin/)
* [Ethereum Lab](/labs/ethereum_lab/)
* [Hyperledger Fabric Lab](/labs/hlf/)

### Instructor Access

* [Instructor login](/instructor/) - single shared instructor login for dynamic lab controls, progress views, and instructor-only quiz management.
"""


def main() -> None:
    index_path = Path("/work/blockchain-course/index.qmd")
    source = index_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in source:
        raise SystemExit(f"Placeholder not found in {index_path}")
    index_path.write_text(source.replace(PLACEHOLDER, BLOCK), encoding="utf-8")


if __name__ == "__main__":
    main()
