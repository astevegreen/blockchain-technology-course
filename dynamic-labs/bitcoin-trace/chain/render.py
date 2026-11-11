"""Fill the lab's two templates from the frozen chain's facts.json, so no transaction ID, address, amount or block
number is typed by hand and a rebuild of the chain cannot leave a stale one behind.

build-chain.sh runs this inside the mempool image after the build:
    python3 render.py <lab dir>
It reads <lab>/quizes/facts.json and writes
    <lab>/chain/lab.template.html     -> <lab>/gateway/static/lab/index.html   (students)
    <lab>/quizes/answers.template.md  -> <lab>/quizes/INSTRUCTOR_ANSWERS.md    (instructors only)
A placeholder is {{path}}, {{path|short}} (the first 8 and last 6 characters) or {{path|flag}} (the SHA-256 of
"course-flag:" and the value, which flags.js checks a student's answer against, so the page never holds the flag).
A path walks facts.json by keys and list positions, e.g. {{tx.t1.by.X0.btc}} or {{tx.t6.in.4.address}}.
An unknown path stops the run.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)(?:\|(short|flag))?\s*\}\}")


def derive(facts):
    """Counts and totals the templates quote."""
    for tx in facts["tx"].values():
        tx["n_in"], tx["n_out"] = len(tx["in"]), len(tx["out"])
    facts["calc"] = {
        "payouts": facts["tx"]["t7"]["n_out"] - 1,
        "deposit_inputs": facts["tx"]["t6"]["n_in"] - 1,
        "swept": facts["tx"]["t6"]["out"][0]["btc"],
    }
    facts["calc"]["d_input_position"] = next(n for n, i in enumerate(facts["tx"]["t6"]["in"]) if i["role"] == "D") + 1
    facts["calc"]["e_input_position"] = next(n for n, i in enumerate(facts["tx"]["t6"]["in"]) if i["role"] == "E") + 1
    facts["calc"]["faucet_deposits"] = facts["tx"]["t6"]["n_in"] - 2
    ransom = facts["tx"]["v1"]["by"]["R1"]["sats"] + facts["tx"]["v2"]["by"]["R2"]["sats"]
    facts["calc"]["ransom_paid"] = f"{ransom / 10**8:.8f}"
    t7 = facts["tx"]["t7"]
    facts["calc"]["change_position"] = next(o["n"] for o in t7["out"] if o["role"] == "H2")
    return facts


def lookup(facts, path):
    node = facts
    for key in path.split("."):
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node


def fill(text, facts):
    def sub(m):
        value = str(lookup(facts, m.group(1)))
        if m.group(2) == "flag":
            return hashlib.sha256(f"course-flag:{value}".encode()).hexdigest()
        return f"{value[:8]}…{value[-6:]}" if m.group(2) else value
    return PLACEHOLDER.sub(sub, text)


def main(lab):
    lab = Path(lab)
    facts = derive(json.loads((lab / "quizes" / "facts.json").read_text(encoding="utf-8")))
    jobs = [(lab / "chain" / "lab.template.html", lab / "gateway" / "static" / "lab" / "index.html"),
            (lab / "quizes" / "answers.template.md", lab / "quizes" / "INSTRUCTOR_ANSWERS.md")]
    for src, dst in jobs:
        dst.write_text(fill(src.read_text(encoding="utf-8"), facts), encoding="utf-8", newline="\n")
        print(f"wrote {dst.relative_to(lab)}")


if __name__ == "__main__":
    main(sys.argv[1])
