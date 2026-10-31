---
name: source
description: Find and add a citation to Blockchain.bib for a claim that has none. Use when a fact needs a source, before cutting or changing a fact for want of one (a review or second look disputing it counts), or before adding any bib entry.
paths:
  - "blockchain-course/lessons/**"
  - "quizes/**"
---
# Adding a source

Every fact cites a `Blockchain.bib` key (CLAUDE.md, rule 4); `docs/build-spec.md` ("Sources and dates") says which
facts carry an "as of" date and which tools may appear. A fact with no source, or one a review disputes, climbs
this whole ladder before it is cut: a true, useful fact lost for want of a search costs the course more than the
search. Truth still comes first: a fact no reputable source supports is corrected or cut.

1. **Look in the bib first**: grep `blockchain-course/lessons/references/Blockchain.bib` for the author, title,
   case or topic. An entry that already supports the claim ends the search.
2. **Search the web**: up to three WebSearch queries in `standard` mode (the claim's key terms, the named case,
   protocol or figure), then one in `extended` mode. Look for the highest tier below.
3. **Read it against the claim** with WebFetch: the passage must state the claim itself, not something near it.
   Note the page, section or paragraph for the slide's Sources line. A figure that differs from the slide takes
   the source's value; name the change in the summary.
4. **Narrow the claim** when the source supports less than the slide says: rewrite the slide to what the passage
   states. On 31 Oct 2026 "a wallet on its own node tells no one" became "asks no server", the claim Electrum
   Personal Server's README makes.
5. **Cut only after steps 1-4 find nothing**: remove or hide the fact, and list it with the queries tried in the
   commit message (the `reviewer` looks there) and on the summary's **Searched, then cut** line.
6. **Write the entry** in the style of its neighbors: key `<author-or-org>_<word>_<year>`, `title`, `author` or
   `organization`, `date`, `url`, and `urldate = {YYYY-MM-DD}`, the day you read it. That date is the "as of" date
   for a fact that changes, and the check refuses a new entry with a `url` and no `urldate`.
7. **Quote the passage** that supports each claim, word for word, with the entry's key and URL: in a sprint on the
   issue ("Implementer: source"), otherwise in the session's summary. The `reviewer` fetches the URL and checks
   the quote; the owner no longer approves new entries (owner's policy, 28 Oct 2026).
8. **Check**: `python tools/check.py`.

Done when every new or disputed claim cites an entry whose passage is quoted, every cut fact is on the
**Searched, then cut** line, and the check passes.

## Source tiers
Cite the highest tier that states the claim:
1. **Primary**: the standard itself (BIP, EIP, RFC), protocol or client documentation and source code, court
   filings and indictments, regulator and Treasury notices, a project's own incident post-mortem, peer-reviewed
   papers.
2. **Research and reference**: analytics firms' published research (Chainalysis, TRM, Elliptic: cited, their
   platforms never featured), textbooks and established reference works.
3. **Established news** reporting a tier 1 or 2 source.

Blogs, forums, Medium posts and AI summaries are leads to a tiered source, never the citation. For Wikipedia, cite
the source its passage cites when that source is reachable.
