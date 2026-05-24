"""
Cryptography lab exercise catalog.

Cryptography runs as a Streamlit app with a page per module. Within
each page, the student picks a scenario via a sidebar radio. Both
the page open AND each scenario change fire a progress beacon, so
the catalog enumerates one exercise per scenario (not per page) —
that way the tracker's percent-complete reflects how many scenarios
the student has actually opened, not just how many module pages
they've landed on.

Beacon route_id format:
  exercise:crypto-<module>-s<n>   — fired when scenario <n> in module
                                    is selected (or the page's default
                                    scenario is rendered)
  surface:home                    — fired by Lab_2_Home.py
"""

from __future__ import annotations


CATALOG = {
    "intro": {
        "title": "Applied Cryptography",
        "summary": (
            "Three modules — Hashing, Merkle Trees, and Symmetric/"
            "Asymmetric Encryption — each with multiple scenarios "
            "the student works through. The tracker counts every "
            "scenario the student opens."
        ),
        "chapters": [
            {
                "id": "crypto-hashing",
                "title": "Hashing",
                "summary": "Hash-function properties, collisions, and entropy.",
            },
            {
                "id": "crypto-merkle",
                "title": "Merkle Trees",
                "summary": "Build and verify Merkle proofs; tamper-evident ledgers.",
            },
            {
                "id": "crypto-symasym",
                "title": "Symmetric & Asymmetric Encryption",
                "summary": "AES vs RSA; signatures, key exchange, hybrid schemes.",
            },
        ],
    },
    "exercises": [
        # Module 1 — Hashing
        {
            "id": "crypto-hashing-s1",
            "chapter": "crypto-hashing",
            "title": "Weak Hash Collisions",
            "goal": "Forge a transaction with the same 4-bit toy hash.",
        },
        {
            "id": "crypto-hashing-s2",
            "chapter": "crypto-hashing",
            "title": "The Avalanche Effect",
            "goal": "Hash near-identical inputs and observe SHA-256 dispersion.",
        },
        {
            "id": "crypto-hashing-s3",
            "chapter": "crypto-hashing",
            "title": "Entropy & Ransomware",
            "goal": "Brute-force a low-entropy seed window to decrypt the file.",
        },
        # Module 2 — Merkle Trees
        {
            "id": "crypto-merkle-s1",
            "chapter": "crypto-merkle",
            "title": "Build a Tree",
            "goal": "Hash transactions into leaves and combine up to a root.",
        },
        {
            "id": "crypto-merkle-s2",
            "chapter": "crypto-merkle",
            "title": "Verify a Proof",
            "goal": "Walk a sibling-hash path and detect a forged transaction.",
        },
        # Module 3 — Symmetric & Asymmetric
        {
            "id": "crypto-symasym-s1",
            "chapter": "crypto-symasym",
            "title": "The Leaked S1 Record",
            "goal": "Encrypt a small record with asymmetric crypto.",
        },
        {
            "id": "crypto-symasym-s2",
            "chapter": "crypto-symasym",
            "title": "The Embassy Collaborator",
            "goal": "Use symmetric crypto for a shared-key channel.",
        },
        {
            "id": "crypto-symasym-s3",
            "chapter": "crypto-symasym",
            "title": "Forged Ambassador Cables",
            "goal": "Use signatures to authenticate a sender.",
        },
        {
            "id": "crypto-symasym-s4",
            "chapter": "crypto-symasym",
            "title": "The 1GB ISR Video",
            "goal": "Hybrid scheme — asymmetric exchange + symmetric bulk.",
        },
    ],
}

EXERCISE_IDS = [ex["id"] for ex in CATALOG["exercises"]]
SURFACE_IDS = ["home"]
