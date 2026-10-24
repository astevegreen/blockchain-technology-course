"""Run queries.sql against one extract folder and print each named query's output.

    python run_queries.py <extract-folder> [query-number ...]

Stands in for the browser page a lab would use (DuckDB's browser build runs the same SQL); needs `pip install duckdb`.
"""
import os
import re
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # DuckDB draws its tables with box characters
    folder = Path(sys.argv[1]).resolve()
    wanted = set(sys.argv[2:])
    sql = (HERE / "queries.sql").read_text(encoding="utf-8")
    setup, *named = re.split(r"^-- name: ", sql, flags=re.M)
    os.chdir(folder)
    con = duckdb.connect()
    con.execute(setup)
    for block in named:
        title, body = block.split("\n", 1)
        if wanted and title.split(".")[0] not in wanted:
            continue
        print(f"\n## {title}")
        con.sql(body.strip().rstrip(";")).show(max_rows=200, max_width=250)


if __name__ == "__main__":
    main()
