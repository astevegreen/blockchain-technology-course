"""Check that the browser page showed what DuckDB itself gives for each query: same columns, rows and values.

    python page_check.py <lab> [<lab> ...]      (after node test-page.mjs <lab>; needs `pip install duckdb`)

Runs the lab's queries.sql over its data folder the way run_queries.py does, reads every value as DuckDB's own text
(as the page does), and compares with dist/results-<lab>.json. Prints one line per query; exits 1 on any difference.
"""
import json
import os
import re
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent


def check(lab):
    spec = json.loads((HERE / "labs" / f"{lab}.json").read_text(encoding="utf-8"))
    page = json.loads((HERE / "dist" / f"results-{lab}.json").read_text(encoding="utf-8"))
    sql = (HERE / spec["queries"]).resolve().read_text(encoding="utf-8")
    setup, *named = re.split(r"^-- name: ", sql, flags=re.M)
    os.chdir((HERE / spec["data"]).resolve())
    con = duckdb.connect()
    con.execute(setup)
    ok = True
    print(f"{lab}: page {page['engine']}; here DuckDB {duckdb.__version__}")
    for block, shown in zip(named, page["results"], strict=True):
        title, body = block.split("\n", 1)
        body = body.strip().rstrip(";")
        plain = con.sql(body)
        as_text = con.sql(f"SELECT COLUMNS(*)::VARCHAR FROM (\n{body}\n)")
        rows = [list(r) for r in as_text.fetchall()]
        same = (title.strip() == shown["title"] and as_text.columns == shown["columns"] and rows == shown["rows"]
                and len(plain.fetchall()) == len(rows))
        ok &= same
        print(f"  {'same' if same else 'DIFFERENT'}: {title.strip()} ({len(rows)} rows x {len(as_text.columns)} columns)")
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    results = [check(lab) for lab in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
