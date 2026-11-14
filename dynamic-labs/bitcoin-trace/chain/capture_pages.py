"""Write the Bitcoin trace lab's saved pages (gateway/static/fallback/index.html) from the frozen chain's build output.

build-chain.sh runs this inside the mempool image after build-steps.py, with the build's out/ folder:
    python3 capture_pages.py <out dir> <html file>

The page shows what the explorer shows for each lab transaction (inputs with address, type and value; outputs; fee and
size) and, for each address those transactions touch, what it received and sent in them (the faucet's mined coins are
not listed, so its rows are not its whole history). Like the explorer, it carries no labels.
"""
import html
import json
import sys
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

TYPES = {
    "witness_v0_keyhash": "P2WPKH (V0_P2WPKH)",
    "witness_v1_taproot": "P2TR (V1_P2TR)",
    "scripthash": "P2SH",
}


def sats(btc):
    return round(Decimal(str(btc)) * 100_000_000)


def btc(value):
    return f"{Decimal(str(value)):.8f} BTC"


def code(text):
    return f"<code>{html.escape(str(text))}</code>"


def addr_link(address):
    return f'<a href="#{address}">{code(address)}</a>'


def row(label, value):
    return f"<tr><th>{label}</th><td>{value}</td></tr>"


def tx_section(tx, height):
    when = datetime.fromtimestamp(tx["blocktime"], timezone.utc).strftime("%d %b %Y %H:%M:%S UTC")
    fee_sats = sats(tx["fee"])
    parts = [f'<section id="{tx["txid"]}"><h2>Transaction in block {height}</h2><table>',
             row("Transaction ID", code(tx["txid"])),
             row("Block", f'{height} ({when})'),
             row("Fee", f'{btc(tx["fee"])} ({fee_sats:,} sats, {fee_sats / tx["vsize"]:.2f} sat/vB)'),
             row("Size", f'{tx["vsize"]} vB ({tx["weight"]} weight units)'),
             row("Locktime", tx["locktime"]),
             "</table>"]
    parts.append(f"<h3>Inputs ({len(tx['vin'])})</h3><table class=\"role-input\">")
    for n, vin in enumerate(tx["vin"]):
        prev = vin["prevout"]["scriptPubKey"]
        parts.append(row(f"Input {n}", f'{addr_link(prev["address"])}<br>'
                         f'{TYPES.get(prev["type"], prev["type"])}, {btc(vin["prevout"]["value"])}<br>'
                         f'spends output {vin["vout"]} of {code(vin["txid"])}'))
    parts.append("</table>")
    parts.append(f"<h3>Outputs ({len(tx['vout'])})</h3><table class=\"role-output\">")
    for vout in tx["vout"]:
        spk = vout["scriptPubKey"]
        parts.append(row(f'Output {vout["n"]}', f'{addr_link(spk["address"])}<br>'
                         f'{TYPES.get(spk["type"], spk["type"])}, {btc(vout["value"])}'))
    parts.append("</table></section>")
    return "\n".join(parts)


def address_sections(txs, heights, order):
    seen = {}
    for name in order:
        tx = txs[name]
        for vin in tx["vin"]:
            spk = vin["prevout"]["scriptPubKey"]
            seen.setdefault(spk["address"], [spk["type"], []])[1].append(
                (heights[name], tx["txid"], "sent", vin["prevout"]["value"]))
        for vout in tx["vout"]:
            spk = vout["scriptPubKey"]
            seen.setdefault(spk["address"], [spk["type"], []])[1].append(
                (heights[name], tx["txid"], "received", vout["value"]))
    parts = []
    for address in sorted(seen):
        kind, rows = seen[address]
        parts.append(f'<section id="{address}"><h2>Address {code(address)}</h2><table>'
                     + row("Type", TYPES.get(kind, kind))
                     + "".join(row(f"Block {h}", f'{d} {btc(v)} in <a href="#{t}">{code(t)}</a>')
                               for h, t, d, v in sorted(rows))
                     + "</table></section>")
    return parts, sorted(seen)


def main(out_dir, html_file):
    out = Path(out_dir)
    facts = json.loads((out / "facts.json").read_text())
    order = facts["order"]
    txs = {n: json.loads((out / f"tx-{n}.json").read_text()) for n in order}
    heights = {n: facts["tx"][n]["height"] for n in order}
    addresses, known = address_sections(txs, heights, order)
    nav = "".join(f'<li><a href="#{txs[n]["txid"]}">Block {heights[n]}: {txs[n]["txid"][:10]}...</a></li>'
                  for n in order)
    index = json.dumps(known + [txs[n]["txid"] for n in order])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saved explorer pages: Bitcoin trace lab chain</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 72rem; margin: 0 auto; padding: 1rem; color: #1b1b1b; }}
h1 {{ font-size: 1.5rem; }} h2 {{ font-size: 1.1rem; margin-top: 2rem; border-top: 1px solid #ccc; padding-top: 1rem; }}
h3 {{ font-size: 1rem; margin-bottom: .25rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ text-align: left; vertical-align: top; width: 14rem; padding: .25rem .5rem .25rem 0; font-weight: 600; }}
td {{ padding: .25rem 0; word-break: break-all; }}
code {{ font-size: .9em; }}
nav li {{ display: inline; margin-right: .75rem; }}
input {{ font: inherit; padding: .3rem .5rem; width: 100%; max-width: 40rem; box-sizing: border-box; }}
.note {{ background: #fff6dd; padding: .5rem 1rem; border-left: 4px solid #e0a800; }}
/* Inputs and outputs in the course's shared look (blockchain-course/assets/labs/shared/look.css). */
.role-input th, tr.role-input th {{ border-left: 4px solid #0072b2; background: #e1effa; padding-left: .5rem; }}
.role-output th, tr.role-output th {{ border-left: 4px solid #009e73; background: #dff4ec; padding-left: .5rem; }}
@media (max-width: 40rem) {{ th {{ width: auto; display: block; }} td {{ display: block; padding-bottom: .5rem; }} }}
</style>
</head>
<body>
<h1>Saved explorer pages: Bitcoin trace lab chain, blocks 1-{facts["height"]}</h1>
<p class="note">Use this page when the explorer or the lab chain is down. It shows the fields the explorer
shows for the lab's transactions and every address they touch, read from the same node. Your worksheet
questions have the same answers here. Times are UTC. An address lists only the lab's transactions:
the coins the faucet mined are left out. Start from the ransom addresses in your worksheet.</p>
<form id="search"><label for="q"><b>Search</b> an address or transaction ID</label>
<input id="q" autocomplete="off" spellcheck="false"><p id="miss" class="note" hidden></p></form>
<nav><ul>{nav}</ul></nav>
{"".join(tx_section(txs[n], heights[n]) for n in order)}
{"".join(addresses)}
<script>
const known = new Set({index});
document.getElementById("search").addEventListener("submit", (e) => {{
  e.preventDefault();
  const q = document.getElementById("q").value.trim(), miss = document.getElementById("miss");
  miss.hidden = known.has(q);
  if (known.has(q)) {{ location.hash = q; return; }}
  miss.textContent = /^(bc1|3)/.test(q)
    ? "No transactions on this chain touch that address."
    : "Not found. Paste a whole address (bc1... or 3...) or a 64-character transaction ID.";
}});
</script>
</body>
</html>
"""
    Path(html_file).write_text(page)
    print(f"wrote {html_file}: {len(order)} transactions, {len(known)} addresses")


if __name__ == "__main__":
    main(*sys.argv[1:3])
