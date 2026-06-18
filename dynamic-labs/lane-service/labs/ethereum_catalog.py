"""
Ethereum lab exercise catalog.

Defines granular exercise IDs covering the full SPA: learn trail,
explore missions, simulator, live network, CLI, beacon chain lab,
contract builder lab, and tokenization lab.
"""

from __future__ import annotations

CATALOG = {
    "intro": {
        "title": "Ethereum Immersive",
        "summary": (
            "A live Proof-of-Stake beacon-chain simulator and a GUI smart-contract "
            "workshop (compile, deploy, and interact — no CLI), all against a shared "
            "Hardhat node with an on-chain explorer."
        ),
    },
    "exercises": [
        # Active course surface only. Keep this catalog aligned with the
        # learner-accessible flows so the instructor progress panel stays accurate.
        # Re-add exercise IDs here if additional surfaces are enabled in App.jsx.

        # --- Live dashboard ---
        {"id": "eth-live", "chapter": "core", "title": "Live Network"},

        # --- Beacon Chain Lab ---
        {"id": "eth-beacon-lab", "chapter": "beacon", "title": "Beacon Chain Lab"},

        # --- Smart Contract Lab (GUI: write -> deploy -> interact) ---
        {"id": "eth-contract-write", "chapter": "contract-builder", "title": "Write / Choose a Contract"},
        {"id": "eth-contract-compile", "chapter": "contract-builder", "title": "Compile Contract"},
        {"id": "eth-contract-deploy", "chapter": "contract-builder", "title": "Deploy from Wallet"},
        {"id": "eth-contract-review-class-contracts", "chapter": "contract-builder", "title": "Review Class Contracts"},
        {"id": "eth-contract-interact", "chapter": "contract-builder", "title": "Interact On-Chain"},
        {"id": "eth-contract-peer-open", "chapter": "contract-builder", "title": "Find a Peer Contract"},
        {"id": "eth-contract-peer-interact", "chapter": "contract-builder", "title": "Interact with Peer Contract"},
        {"id": "eth-contract-event-receipt", "chapter": "contract-builder", "title": "Inspect Event Receipt"},
        {"id": "eth-contract-bytecode", "chapter": "contract-builder", "title": "Inspect Contract Bytecode"},
        {"id": "eth-contract-disasm", "chapter": "contract-builder", "title": "Inspect Contract Disassembly"},

        # --- Tokenization Lab ---
        {"id": "eth-token-erc721", "chapter": "tokenization", "title": "Load ERC-721 Classroom Contracts"},
        {"id": "eth-token-metadata", "chapter": "tokenization", "title": "Claim Static-Art Theme"},
        {"id": "eth-token-deploy", "chapter": "tokenization", "title": "Mint Five NFT Variants"},
        {"id": "eth-token-evm", "chapter": "tokenization", "title": "Verify Ownership and Metadata"},
        {"id": "eth-token-transfer", "chapter": "tokenization", "title": "Transfer an NFT"},
        {"id": "eth-token-sale", "chapter": "tokenization", "title": "List or Buy an NFT"},

        # --- Fungible Token Arcade Lab ---
        {"id": "eth-ft-load", "chapter": "tokenization", "title": "Load ERC-20 Arcade Contracts"},
        {"id": "eth-ft-buy", "chapter": "tokenization", "title": "Buy 1 ARC"},
        {"id": "eth-ft-approve", "chapter": "tokenization", "title": "Approve Arcade Vault"},
        {"id": "eth-ft-play", "chapter": "tokenization", "title": "Spend ARC to Start a Game"},
        {"id": "eth-ft-burn-verify", "chapter": "tokenization", "title": "Verify Burn and Session"},
    ],
}

EXERCISE_IDS = [ex["id"] for ex in CATALOG["exercises"]]
SURFACE_IDS = ["home"]
