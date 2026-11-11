#!/usr/bin/env python3

from pathlib import Path


PLACEHOLDER = "<!-- DYNAMIC_RUNTIME_LINKS -->"

# BEGIN GENERATED BLOCK (tools/lab_manifest.py: edit the manifests, then run it with --write)
BLOCK = """## Dynamic Labs

Use this section when the packaged VM or cloud lab stack is running.

### Student Starting Point

* [Student lab and quiz login](/quiz/student/) - start here to get or enter a student identifier and access assigned dynamic work.

### Student Lab Workspaces

Use these links after the instructor tells the class which lab is active. They are listed in the order of the days that use them.

* Day 1: [Social Trust Lab: The Insider](/exercises/insider/) and [Explorer Lab](/labs/explorer/)
* Day 2: [Wallet Lab](/labs/wallet/)
* Day 3: [Token Lab](/labs/tokens/)
* Day 4: [Exchange and Bridge Lab](/labs/dex/)
* Days 5 and 9: [Tron Lab](/labs/tron/)
* Day 5: [Hyperledger Fabric Lab](/labs/hlf/)
* Day 6: [Bitcoin Trace Lab](/labs/bitcoin-trace/)
* Day 7: [CoinJoin Trace Lab](/labs/coinjoin-trace/) and [Hide and trace (team game)](/labs/hide-and-trace/)
* Day 8: [Cross-Chain Lab](/labs/cross-chain/)
* Day 10: [Final Trace Lab](/labs/final-trace/)

### Labs outside the ten-day schedule

* [Byzantine Generals Lab](/exercises/bgp/)
* [Cryptography Lab](/labs/cryptography/)
* [Consensus Lab](/labs/consensus/)
* [Bitcoin Lab](/labs/bitcoin/)

### Instructor Access

* [Instructor login](/instructor/) - single shared instructor login for dynamic lab controls, progress views, and instructor-only quiz management.
"""
# END GENERATED BLOCK


def main() -> None:
    index_path = Path("/work/blockchain-course/index.qmd")
    source = index_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in source:
        raise SystemExit(f"Placeholder not found in {index_path}")
    index_path.write_text(source.replace(PLACEHOLDER, BLOCK), encoding="utf-8")


if __name__ == "__main__":
    main()
