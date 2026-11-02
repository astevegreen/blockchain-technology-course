"""Writes the final trace's saved Tron results page: every query in queries/d10.sql with its output on snapshot/.
A copy of the Tron lab's build/saved_results.py (tron/build), for this lab's one query set.

    python build/saved_results.py [d10]    (from dynamic-labs/final-trace; needs duckdb 1.4.3)

It writes static/fallback/tron/index.html.

The query page splits queries.sql the same way and shows every value as DuckDB's own text, so a student who
reads this page instead of the query page reads the same answers. Rerun it whenever the queries or the
snapshot change; the lab's tests compare the two.
"""
import html
import json
import os
import re
import sys

import duckdb

# The query page runs DuckDB-wasm 1.32.0, whose engine is DuckDB 1.4.3; another version can print values differently.
ENGINE = "1.4.3"
if duckdb.__version__ != ENGINE:
    sys.exit(f"saved_results.py needs duckdb {ENGINE}, the query page's engine (found {duckdb.__version__})")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = {
    "d10": ("snapshot", os.path.join("static", "fallback", "tron", "index.html")),
}


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


def write(name):
    snapshot, out = (os.path.join(HERE, p) for p in LABS[name])
    with open(os.path.join(HERE, "queries", f"{name}.sql"), encoding="utf-8") as f:
        setup, named = split_queries(f.read())
    with open(os.path.join(HERE, "query-page", "labs", f"{name}.json"), encoding="utf-8") as f:
        lab = json.load(f)
    os.chdir(snapshot)
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
<title>Saved query results: final trace, Tron leg</title>
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
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"{out}: {len(named)} queries")


if __name__ == "__main__":
    for name in sys.argv[1:] or LABS:
        write(name)
