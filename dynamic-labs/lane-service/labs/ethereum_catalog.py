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
            "A multi-view SPA covering Proof-of-Stake fundamentals, "
            "smart contract development, ERC-721 tokenization, forensics, "
            "and a live beacon-chain simulator — all against a shared "
            "Hardhat node."
        ),
    },
    "exercises": [
        # --- Learn Trail ---
        {"id": "eth-trail-intro", "chapter": "learn-trail", "title": "Orientation"},
        {"id": "eth-trail-concepts", "chapter": "learn-trail", "title": "Concepts"},
        {"id": "eth-trail-explore", "chapter": "learn-trail", "title": "Explore Missions"},

        # --- Explore Missions (quiz / mini-lab) ---
        {"id": "eth-explore-staking", "chapter": "explore", "title": "Understanding Staking"},
        {"id": "eth-explore-validators", "chapter": "explore", "title": "Validator Responsibilities"},
        {"id": "eth-explore-slashing", "chapter": "explore", "title": "Slashing: The Penalty System"},
        {"id": "eth-explore-defi", "chapter": "explore", "title": "DeFi: Staking Beyond Validation"},
        {"id": "eth-explore-rewards", "chapter": "explore", "title": "Staking Rewards Economics"},
        {"id": "eth-explore-attack-cost", "chapter": "explore", "title": "Attack Cost Scenario"},
        {"id": "eth-explore-chain", "chapter": "explore", "title": "Observe the Chain"},
        {"id": "eth-explore-address", "chapter": "explore", "title": "Decode an Address"},

        # --- Simulator / Live / Tokens ---
        {"id": "eth-sim", "chapter": "core", "title": "PoS Validator Simulator"},
        {"id": "eth-live", "chapter": "core", "title": "Live Network"},
        {"id": "eth-tokens", "chapter": "core", "title": "Token Gallery"},

        # --- CLI & Diagnostics ---
        {"id": "eth-cli", "chapter": "cli", "title": "CLI Labs Reference"},
        {"id": "eth-diagnostics", "chapter": "cli", "title": "Diagnostics"},

        # --- Beacon Chain Lab ---
        {"id": "eth-beacon-lab", "chapter": "beacon", "title": "Beacon Chain Lab"},

        # --- Contract Builder Lab (6 steps) ---
        {"id": "eth-contract-write", "chapter": "contract-builder", "title": "Write Your Contract"},
        {"id": "eth-contract-prereqs", "chapter": "contract-builder", "title": "Prerequisites"},
        {"id": "eth-contract-deploy", "chapter": "contract-builder", "title": "Deploy"},
        {"id": "eth-contract-share", "chapter": "contract-builder", "title": "Share"},
        {"id": "eth-contract-interact", "chapter": "contract-builder", "title": "Interact (Partner)"},
        {"id": "eth-contract-verify", "chapter": "contract-builder", "title": "Verify"},

        # --- Tokenization Lab (6 steps) ---
        {"id": "eth-token-erc721", "chapter": "tokenization", "title": "Read & Explain ERC-721"},
        {"id": "eth-token-evm", "chapter": "tokenization", "title": "EVM Deep Dive: mint()"},
        {"id": "eth-token-deploy", "chapter": "tokenization", "title": "Deploy & Trace"},
        {"id": "eth-token-metadata", "chapter": "tokenization", "title": "Metadata & Data URI"},
        {"id": "eth-token-transfer", "chapter": "tokenization", "title": "Transfer to Another Student"},
        {"id": "eth-token-sale", "chapter": "tokenization", "title": "Build a Sale Contract"},
    ],
}

EXERCISE_IDS = [ex["id"] for ex in CATALOG["exercises"]]
SURFACE_IDS = ["home"]
