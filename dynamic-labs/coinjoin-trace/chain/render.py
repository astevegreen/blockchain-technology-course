"""Fill the lab's two templates from the frozen chain's facts.json, so no transaction ID, address, amount or block
number is typed by hand and a rebuild of the chain cannot leave a stale one behind.

build-chain.sh runs this inside the mempool image after the build:
    python3 render.py <lab dir>
It reads <lab>/quizes/facts.json and writes
    <lab>/chain/lab.template.html     -> <lab>/gateway/static/lab/index.html   (students)
    <lab>/quizes/answers.template.md  -> <lab>/quizes/INSTRUCTOR_ANSWERS.md    (instructors only)
A placeholder is {{path}} or {{path|short}} (the first 8 and last 6 characters). A path walks facts.json by keys and
list positions, e.g. {{tx.t1.by.C1.btc}} or {{tx.sweep.in.2.address}}. An unknown path stops the run.
"""
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)(?:\|(short))?\s*\}\}")


def derive(facts):
    """Counts and totals the templates quote."""
    for tx in facts["tx"].values():
        tx["n_in"], tx["n_out"] = len(tx["in"]), len(tx["out"])
    tx = facts["tx"]
    mx, pool = tx["dep"]["by"]["MX"], tx["sweep"]["out"][0]
    payout = tx["payout"]
    facts["calc"] = {
        "j0_fee_per_input": tx["j0"]["fee"] // tx["j0"]["n_in"],
        "crowd_gap": tx["n1"]["height"] - tx["j3"]["height"],
        "late_gap": tx["late"]["height"] - tx["j3"]["height"],
        "j3_unspent": tx["j3"]["n_out"] - 1 - sum(1 for n in facts["order"] if n.startswith("n")),
        "deposits": tx["sweep"]["n_in"],
        "mx_position": next(n for n, i in enumerate(tx["sweep"]["in"]) if i["role"] == "MX") + 1,
        "pool_btc": pool["btc"],
        "deposit_total": f"{sum(i['sats'] for i in tx['sweep']['in']) / 10**8:.8f}",
        "mx_share": f"{100 * mx['sats'] / sum(i['sats'] for i in tx['sweep']['in']):.0f}",
        "withdrawals": payout["n_out"] - 1,
        "w_less": f"{100 * (mx['sats'] - payout['by']['W']['sats']) / mx['sats']:.1f}",
        "w2_less": f"{100 * (mx['sats'] - payout['by']['W2']['sats']) / mx['sats']:.1f}",
        "ransom_to_m1": f"{(tx['m1']['by_in']['A1']['sats'] + tx['m1']['by_in']['B1']['sats'] + tx['m1']['by_in']['C1']['sats']) / 10**8:.8f}",
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
    jobs = [(lab / "chain" / "lab.template.html", lab / "gateway" / "static" / "lab" / "index.html"),
            (lab / "quizes" / "answers.template.md", lab / "quizes" / "INSTRUCTOR_ANSWERS.md")]
    for src, dst in jobs:
        dst.write_text(fill(src.read_text(), facts), newline="\n")
        print(f"wrote {dst.relative_to(lab)}")


if __name__ == "__main__":
    main(sys.argv[1])
