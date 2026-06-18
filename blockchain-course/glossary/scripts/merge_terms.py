#!/usr/bin/env python3
"""Merge per-lesson candidate files into the canonical glossary."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = ROOT / "glossary"
LESSON_TERMS = GLOSSARY / "lesson_terms"
SLIDE_INDEX = GLOSSARY / "slide-index.yml"
OUT = GLOSSARY / "terms.yml"
DUPES = GLOSSARY / "duplicates.md"

MODIFIER_OVERRIDES = {
    ("bitcoin", "blockchain platform"): None,
    ("ethereum", "blockchain platform"): None,
    ("hyperledger", "blockchain framework"): None,
    ("consensus", "blockchain mechanism"): None,
    ("transaction", "blockchain"): None,
    ("token", "blockchain"): None,
    ("forensic analysis", "blockchain"): None,
    ("network threat", "blockchain"): None,
    ("scalability", "blockchain"): None,
}

MODIFIER_CANONICALS = [
    ("hyperledger fabric", "Hyperledger Fabric"),
    ("bitcoin", "Bitcoin"),
    ("ethereum", "Ethereum"),
    ("evm", "Ethereum"),
    ("solidity", "Ethereum"),
    ("proof of work", "Proof of Work"),
    ("pow", "Proof of Work"),
    ("proof of stake", "Proof of Stake"),
    ("pos", "Proof of Stake"),
    ("stablecoin", "Stablecoins"),
    ("cbdc", "CBDCs"),
    ("smart contract", "Smart Contracts"),
    ("permissioned", "Permissioned Ledgers"),
    ("forensic", "Forensics"),
    ("cryptography", "Cryptography"),
    ("crypto", "Cryptography"),
]

OVERLOADED_MODIFIERS = {
    "account": {"Ethereum"},
    "account model": {"Ethereum"},
    "address": {"Bitcoin", "Ethereum"},
    "attestation": {"Ethereum", "Proof of Stake"},
    "block": {"Bitcoin", "Ethereum"},
    "block proposer": {"Ethereum", "Proof of Stake"},
    "checkpoint": {"Ethereum", "Proof of Stake"},
    "client": {"Ethereum"},
    "committee": {"Ethereum", "Proof of Stake"},
    "epoch": {"Ethereum", "Proof of Stake"},
    "finality": {"Ethereum", "Proof of Stake"},
    "fork choice rule": {"Bitcoin", "Ethereum", "Proof of Stake"},
    "full node": {"Bitcoin", "Ethereum"},
    "gas": {"Ethereum"},
    "light client": {"Bitcoin", "Ethereum"},
    "mempool": {"Bitcoin", "Ethereum"},
    "nonce": {"Bitcoin", "Ethereum", "Cryptography"},
    "node": {"Bitcoin", "Ethereum", "Hyperledger Fabric", "Permissioned Ledgers"},
    "slashing": {"Ethereum", "Proof of Stake"},
    "slot": {"Ethereum", "Proof of Stake"},
    "transaction": {"Bitcoin", "Ethereum"},
    "utxo model": {"Bitcoin"},
    "validator": {"Ethereum", "Proof of Stake"},
}

TERM_CANONICALS = {
    "2008 global financial crisis": "2008 financial crisis",
    "a cypherpunks manifesto": "Cypherpunk Manifesto",
    "account model ethereum": "Account model",
    "account model ethereum accounting": "Account model",
    "account model ethereum transaction model": "Account model",
    "account-centric model": "Account model",
    "aml": "Anti-money laundering",
    "kyc": "Know your customer",
    "kyc/aml": "KYC/AML",
    "pow": "Proof of Work",
    "pos": "Proof of Stake",
    "proof-of-work": "Proof of Work",
    "proof-of-stake": "Proof of Stake",
}

CONTEXT_PREFIX_TERMS = {
    "address",
    "attestation",
    "block",
    "block proposer",
    "checkpoint",
    "client",
    "committee",
    "epoch",
    "finality",
    "full node",
    "light client",
    "mempool",
    "node",
    "nonce",
    "slashing",
    "slot",
    "transaction",
    "validator",
}


def norm(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^a-z0-9 ()/-]", "", value)
    return value


def canonical_term(term: str, modifier: Any) -> tuple[str, Any]:
    raw = str(term or "").strip()
    raw_norm = norm(raw)
    if raw_norm in TERM_CANONICALS:
        return TERM_CANONICALS[raw_norm], modifier

    for prefix, canonical_modifier in (
        ("bitcoin ", "Bitcoin"),
        ("ethereum ", "Ethereum"),
        ("hyperledger fabric ", "Hyperledger Fabric"),
    ):
        if raw_norm.startswith(prefix):
            rest = raw_norm[len(prefix) :].strip()
            if rest in CONTEXT_PREFIX_TERMS:
                return raw[len(prefix) :].strip(), canonical_modifier
    return raw, modifier


def display_term(item: dict[str, Any]) -> str:
    term = str(item.get("term", "")).strip()
    modifier = item.get("modifier")
    if modifier in (None, "", "null"):
        return term
    return f"{term} ({modifier})"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def slide_lookup() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    if not SLIDE_INDEX.exists():
        return {}, {}
    data = load_yaml(SLIDE_INDEX)
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    normalized: dict[tuple[str, str], dict[str, Any]] = {}
    for lesson in data.get("lessons", []):
        lesson_id = lesson.get("lesson_id")
        for slide in lesson.get("slides", []):
            source = {
                "lesson_id": lesson_id,
                "lesson_title": lesson.get("lesson_title"),
                "source_path": lesson.get("source_path"),
                "slide_number": slide.get("number"),
                "slide_heading": slide.get("heading"),
                "slide_anchor": slide.get("anchor"),
                "href": slide.get("href"),
            }
            lookup[(lesson_id, slide.get("heading"))] = source
            normalized[(lesson_id, norm(str(slide.get("heading", ""))))] = source
    return lookup, normalized


def course_order() -> dict[tuple[str, str], tuple[int, int]]:
    if not SLIDE_INDEX.exists():
        return {}
    data = load_yaml(SLIDE_INDEX)
    order: dict[tuple[str, str], tuple[int, int]] = {}
    for lesson_idx, lesson in enumerate(data.get("lessons", []), start=1):
        lesson_id = lesson.get("lesson_id")
        for slide in lesson.get("slides", []):
            order[(lesson_id, slide.get("heading"))] = (lesson_idx, int(slide.get("number", 9999)))
    return order


def normalize_modifier(term: str, modifier: Any) -> Any:
    if modifier in (None, "", "null"):
        return None
    text = str(modifier).strip()
    override = MODIFIER_OVERRIDES.get((norm(term), norm(text)), text)
    if override is None:
        return None
    override_norm = norm(str(override))
    for needle, canonical in MODIFIER_CANONICALS:
        if needle in override_norm:
            return canonical
    return str(override).strip()


def canonical_key(term: str, modifier: Any) -> tuple[str, str]:
    base = norm(term)
    allowed = OVERLOADED_MODIFIERS.get(base, set())
    if modifier in allowed:
        return base, str(modifier)
    return base, ""


def enrich(
    item: dict[str, Any],
    lesson_file: dict[str, Any],
    lookup: dict[tuple[str, str], dict[str, Any]],
    normalized_lookup: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    item = dict(item)
    raw_term = str(item.get("term", "")).strip()
    raw_modifier = item.get("modifier")
    canonical, modifier = canonical_term(raw_term, raw_modifier)
    item["term"] = canonical
    item["modifier"] = normalize_modifier(item["term"], modifier)
    item["canonical_key"] = canonical_key(item["term"], item["modifier"])
    if not item["canonical_key"][1]:
        item["modifier"] = None
    item["display"] = display_term(item)
    item["aliases"] = [str(v).strip() for v in item.get("aliases", []) if str(v).strip()]
    original_display = display_term({"term": raw_term, "modifier": raw_modifier})
    if original_display and norm(original_display) != norm(item["display"]):
        item["aliases"].append(original_display)
    item["tags"] = sorted({str(v).strip().lower() for v in item.get("tags", []) if str(v).strip()})
    item["definition"] = str(item.get("definition", "")).strip()
    item["context"] = str(item.get("context", "")).strip()
    item["confidence"] = str(item.get("confidence", "medium")).strip().lower()
    lesson_id = str(lesson_file.get("lesson_id", "")).strip()
    slide_heading = str(item.get("slide_heading", "")).strip()
    source = lookup.get((lesson_id, slide_heading), {})
    if not source:
        source = normalized_lookup.get((lesson_id, norm(slide_heading)), {})
        if source:
            slide_heading = source.get("slide_heading", slide_heading)
    item["source"] = {
        "lesson_id": lesson_id,
        "lesson_title": lesson_file.get("lesson_title") or source.get("lesson_title"),
        "source_path": lesson_file.get("source_path") or source.get("source_path"),
        "slide_number": source.get("slide_number"),
        "slide_heading": slide_heading,
        "slide_anchor": source.get("slide_anchor"),
        "href": source.get("href"),
    }
    item.pop("slide_heading", None)
    return item


def main() -> None:
    lookup, normalized_lookup = slide_lookup()
    order = course_order()
    candidates: list[dict[str, Any]] = []
    notes: list[str] = ["# Duplicate and Editorial Notes", ""]

    for path in sorted(LESSON_TERMS.glob("*.yml")):
        doc = load_yaml(path)
        for item in doc.get("terms", []) or []:
            enriched = enrich(item, doc, lookup, normalized_lookup)
            if enriched["term"] and enriched["definition"]:
                candidates.append(enriched)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        grouped[item["canonical_key"]].append(item)

    merged: list[dict[str, Any]] = []
    for key, items in grouped.items():
        def item_order(item: dict[str, Any]) -> tuple[int, int]:
            source = item.get("source", {})
            return order.get((source.get("lesson_id"), source.get("slide_heading")), (9999, 9999))

        items = sorted(items, key=item_order)
        first = dict(items[0])
        aliases = set(first.get("aliases", []))
        tags = set(first.get("tags", []))
        also = []
        definitions = {norm(item.get("definition", "")) for item in items}
        for extra in items[1:]:
            aliases.update(extra.get("aliases", []))
            tags.update(extra.get("tags", []))
            also.append(extra.get("source", {}))
        first["aliases"] = sorted(aliases)
        first["tags"] = sorted(tags)
        first.pop("canonical_key", None)
        if also:
            first["also_appears"] = also
        merged.append(first)
        if len(items) > 1 and len(definitions) > 1:
            notes.append(f"## {first['display']}")
            notes.append("")
            notes.append("Multiple definitions were proposed. Kept the earliest course appearance.")
            for item in items:
                src = item.get("source", {})
                notes.append(
                    f"- `{src.get('lesson_id')}` / {src.get('slide_heading')}: {item.get('definition')}"
                )
            notes.append("")

    merged = sorted(merged, key=lambda item: norm(item["display"]))
    data = {
        "generated_by": "glossary/scripts/merge_terms.py",
        "term_count": len(merged),
        "terms": merged,
    }
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    if len(notes) == 2:
        notes.append("No conflicting duplicate definitions were found.")
        notes.append("")
    DUPES.write_text("\n".join(notes), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(merged)} terms")


if __name__ == "__main__":
    main()
