---
name: source
description: Find and add a citation to Blockchain.bib for a claim that has none. Use when a fact needs a source, or before adding any bib entry.
paths:
  - "blockchain-course/lessons/references/**"
---
# Adding a source

Every fact cites a `Blockchain.bib` key (CLAUDE.md, rule 4); `docs/build-spec.md` ("Sources and dates") says which
facts carry an "as of" date and which tools may appear. This is the order.

1. **Look in the bib first**: grep `blockchain-course/lessons/references/Blockchain.bib` for the author, title,
   case or topic. An entry that already supports the claim ends the search.
2. **Find the primary source**: the court filing, regulator notice, protocol documentation, incident post-mortem or
   peer-reviewed paper, ahead of news coverage of it. A commercial analytics firm's research may be cited; its
   platform is never featured.
3. **Read it against the claim**: the passage must state the claim itself, not something near it. Note the page,
   section or paragraph for the slide's Sources line. A figure that differs from the slide goes to the owner.
4. **Write the entry** in the style of its neighbors: key `<author-or-org>_<word>_<year>`, `title`, `author` or
   `organization`, `date`, `url`, and `urldate = {YYYY-MM-DD}`, the day you read it. That date is the "as of" date
   for a fact that changes, and the check refuses a new entry with a `url` and no `urldate`.
5. **Show the owner** each new entry with the passage that supports the claim, and add it once they approve.
6. **Check**: `python tools/check.py`.

Done when every new claim cites an approved entry and the check passes.
