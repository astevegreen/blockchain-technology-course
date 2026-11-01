"""Writes opening_balance.csv: an address's USDT balance when a snapshot's window opens, from its full history.

    python build/opening_balance.py <extract> <snapshot> <address> <window start>   (needs the duckdb package)

<extract> is a tron-extract.mjs folder that starts at the address's first transfer; the sum of its USDT
movements before <window start> is the balance the window opens with. java-tron reads balances only at the
latest block, so this is how the lab gets a past one. Refuses if the running balance ever goes below zero,
which means the extract starts too late.
"""
import csv
import os
import sys

import duckdb

QUERY = """
WITH m AS (
  SELECT x.time_utc,
         CASE WHEN r.to_addr = $a THEN r.amount::DECIMAL(38, 6) ELSE -r.amount::DECIMAL(38, 6) END AS v,
         sum(v) OVER (ORDER BY x.block::BIGINT, r.seq::INT) AS balance
  FROM read_csv($tr, all_varchar = true) r JOIN read_csv($tx, all_varchar = true) x USING (tx_id)
  WHERE r.asset = 'USDT' AND $a IN (r.from_addr, r.to_addr))
SELECT min(time_utc), count(*) FILTER (WHERE time_utc < $start), coalesce(sum(v) FILTER (WHERE time_utc < $start), 0),
       min(balance)
FROM m
"""


def main(extract, snapshot, address, start):
    first, movements, usdt, lowest = duckdb.execute(QUERY, {
        "a": address, "start": start,
        "tr": os.path.join(extract, "transfers.csv"), "tx": os.path.join(extract, "transactions.csv"),
    }).fetchone()
    if lowest < 0:
        sys.exit(f"{address}: the balance goes below zero, so {extract} starts after its first transfer")
    with open(os.path.join(snapshot, "opening_balance.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["address", "window_start_utc", "usdt", "movements_before", "first_movement_utc"])
        w.writerow([address, start, f"{usdt:.6f}", movements, first])
    print(f"{address}: {usdt:.6f} USDT at {start}, from {movements} movements since {first}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
