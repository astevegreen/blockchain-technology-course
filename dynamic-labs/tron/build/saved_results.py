"""Writes static/fallback/index.html: every query in queries/d5.sql with its output on the snapshot.

    python build/saved_results.py          (from dynamic-labs/tron; needs the duckdb package)

The query page splits queries.sql the same way and shows every value as DuckDB's own text, so a student who
reads this page instead of the query page reads the same answers. Rerun it whenever the queries or the
snapshot change; the lab's tests compare the two.
"""
import html
import json
import os
import re

import duckdb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(HERE, "snapshot")
QUERIES = os.path.join(HERE, "queries", "d5.sql")
LAB = os.path.join(HERE, "query-page", "labs", "d5.json")
OUT = os.path.join(HERE, "static", "fallback", "index.html")


def split_queries(sql):
    """Setup, then (title, body) per "-- name: " block: the query page's splitQueries in app.mjs."""
    setup, *blocks = re.split(r"^-- name: ", sql, flags=re.M)
    named = []
    for block in blocks:
        title, _, body = block.partition("\n")
        named.append((title.strip(), body.strip().rstrip(";")))
    return setup, named


def run(conn, body):
    cur = conn.execute(f"SELECT COLUMNS(*)::VARCHAR FROM (\n{body}\n)")
    return [d[0] for d in cur.description], cur.fetchall()


def main():
    with open(QUERIES, encoding="utf-8") as f:
        setup, named = split_queries(f.read())
    with open(LAB, encoding="utf-8") as f:
        lab = json.load(f)
    os.chdir(SNAPSHOT)
    conn = duckdb.connect()
    conn.execute(setup)
    parts = []
    for i, (title, body) in enumerate(named, 1):
        cols, rows = run(conn, body)
        head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
        cells = "\n".join(
            "<tr>" + "".join("<td class=\"null\">NULL</td>" if v is None else f"<td>{html.escape(v)}</td>" for v in r)
            + "</tr>" for r in rows)
        parts.append(
            f'<section id="q{i}"><h2>{html.escape(title)}</h2>\n'
            f"<details><summary>The query</summary><pre>{html.escape(body)}</pre></details>\n"
            f"<p>{len(rows)} rows</p>\n<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>\n"
            f"{cells}\n</tbody></table></div></section>")
    nav = "".join(f'<li><a href="#q{i}">{html.escape(t.split(":")[0])}</a></li>' for i, (t, _) in enumerate(named, 1))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saved query results: Tron lab</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 0 auto; padding: 1rem; max-width: 110rem; color: #1b1b1b; }}
h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; border-top: 1px solid #ccc; padding-top: .8rem; margin-top: 1.5rem; }}
pre {{ background: #f4f4f4; padding: .6rem; overflow-x: auto; font-size: .85rem; }}
.table-wrap {{ overflow-x: auto; max-height: 30rem; }}
table {{ border-collapse: collapse; font-size: .85rem; }}
th, td {{ border: 1px solid #ccc; padding: .2rem .5rem; text-align: left; white-space: nowrap; }}
th {{ background: #eee; position: sticky; top: 0; }}
td.null {{ color: #999; }}
nav li {{ display: inline; margin-right: .75rem; }}
.note {{ background: #fff6dd; padding: .5rem 1rem; border-left: 4px solid #e0a800; }}
</style>
</head>
<body>
<h1>Saved query results: {html.escape(lab["title"])}</h1>
<p class="note">Use this page when the query page will not load. It shows every query and the output it gives on
the lab's snapshot, so your worksheet questions have the same answers here. {html.escape(lab["as_of"])}</p>
<nav><ul>{nav}</ul></nav>
{chr(10).join(parts)}
<footer><p>Written by build/saved_results.py with DuckDB {duckdb.__version__}.</p></footer>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"{OUT}: {len(named)} queries")


if __name__ == "__main__":
    main()
