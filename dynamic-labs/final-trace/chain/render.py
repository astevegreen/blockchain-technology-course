"""Fill the final trace's two templates from the frozen chain's facts.json, so no transaction ID, address, amount or block
number is typed by hand and a rebuild of the chain cannot leave a stale one behind.

build-chain.sh runs this inside the mempool image after the build:
    python3 render.py <lab dir>
It reads <lab>/quizes/facts.json and writes
    <lab>/chain/lab.template.html     -> <lab>/static/lab/index.html           (students)
    <lab>/quizes/answers.template.md  -> <lab>/quizes/INSTRUCTOR_ANSWERS.md    (instructors only)
A placeholder is {{path}} or {{path|short}} (the first 8 and last 6 characters). A path walks facts.json by keys and
list positions, e.g. {{tx.t4.by.O.btc}} or {{tron.addr.P}}. An unknown path stops the run.
"""
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)(?:\|(short))?\s*\}\}")


def derive(facts):
    """Counts and totals the templates quote."""
    tx = facts["tx"]
    for t in tx.values():
        t["n_in"], t["n_out"] = len(t["in"]), len(t["out"])
    b = tx["t2"]["by"]
    facts["calc"] = {
        "victims_btc": f"{sum(tx[f'v{i}']['by'][f'S{i}']['sats'] for i in range(1, 5)) / 10**8:.8f}",
        "loose_btc": f"{(b['B7']['sats'] + b['B8']['sats']) / 10**8:.8f}",
        "o_input_position": next(n for n, i in enumerate(tx["t5"]["in"]) if i["role"] == "O") + 1,
        "other_deposits": tx["t5"]["n_in"] - 1,
    }
    return facts


def lookup(facts, path):
    node = facts
    for key in path.split("."):
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node


def fill(text, facts):
    def sub(m):
        value = str(lookup(facts, m.group(1)))
        return f"{value[:8]}…{value[-6:]}" if m.group(2) else value
    return PLACEHOLDER.sub(sub, text)


def main(lab):
    lab = Path(lab)
    facts = derive(json.loads((lab / "quizes" / "facts.json").read_text()))
    jobs = [(lab / "chain" / "lab.template.html", lab / "static" / "lab" / "index.html"),
            (lab / "quizes" / "answers.template.md", lab / "quizes" / "INSTRUCTOR_ANSWERS.md")]
    for src, dst in jobs:
        dst.write_text(fill(src.read_text(), facts), newline="\n")
        print(f"wrote {dst.relative_to(lab)}")


if __name__ == "__main__":
    main(sys.argv[1])
