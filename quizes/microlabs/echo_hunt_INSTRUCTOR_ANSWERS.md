# Echo hunt: instructor key

Instructor only (students never receive `quizes/`). Lab: `blockchain-course/assets/labs/echo-hunt/index.html`; design card `docs/lab-cards/echo-hunt.md`. Everything in the game is invented: T-echo, Desk X, the vendors, the story, the dates and the flows.

## What the page records

The page holds no key. It records each team's "came from" pick and reason for the seven cards, builds the stacks, and counts them. The team scores itself against this sheet. Day 9's graded point stays the Tron trace's note: this is practice.

## Each card's origin

| # | Card | Origin | Accepted reasons |
| --- | --- | --- | --- |
| 1 | Treasury release, 3 Mar | The release itself ("nothing earlier: an original record") | It is the government's own decision; nothing earlier on the list. |
| 2 | Open label set, added 3 Mar, basis "OFAC's SDN list" | Card 1 | The set says its basis is OFAC's list, which is the release's listing. A label set built from the SDN list copies it (`@b10c_ofacaddresses_2026`, as of 1 Nov 2026). |
| 3 | News story, 4 Mar | Card 1 | It quotes the release. |
| 4 | Vendor A tag, first seen 4 Mar, basis not stated | "Basis unknown" | Either reason scores: "basis unknown, so one unverified label, Low, not a second line", or "dated the day after the release, so likely an echo" (a vendor's clustering can draw on leaks, court documents and partnerships: `@sterlingov_cadc_2026`). |
| 5 | Vendor B tag, 6 Mar, source field "Vendor A" | Card 4 (so also "basis unknown") | Its own source field names Vendor A, and Vendor A states no basis. |
| 6 | Team's flow summary | The chain | It reads the address's own transactions. |
| 7 | Vendor C tag, 5 Mar, "exchange hot wallet" | The chain | Its stated basis is the sweeps the address receives: the same transactions card 6 reads. |
| 8 (twist) | The freeze, two hours after the release | Card 1 | Tether says it acted in coordination with OFAC (`@tether_freeze344m_2026`), so its reason is the listing. A freeze for the issuer's own reasons would be a second origin. |

The expected stacks for cards 1 to 7: {1, 2, 3} on the release; {4, 5} in "basis unknown"; {6, 7} on the chain. Known origins: two (the release, the chain). The five cards that name T-echo as Desk X's address (1 to 5) make one line for certain, and at most one unverified label.

## The prediction

Correct choice: (c), one per origin. The page maps the team's stacks of cards 1 to 5 to a choice: 5 stacks reads as (a), 4 as (b), anything else as (c); one stack gives no verdict, because it fits both (d) and Vendor A traced to the release (which the card accepts). Ask a one-stack team for its reasons: (d) would miss that Vendor A states no basis and the flows are a second origin.

## The twist

Answer: no, the freeze echoes the release. It is a fact that USDT blacklisted the address, but its reason is what the issuer says, and here that is the release. The freeze moves neither the count of lines nor the confidence word.

## Scoring (owner's design, 10 Nov 2026)

| Item | Points |
| --- | --- |
| Each card traced to its origin with its reason (eight cards, with the freeze) | +1 each |
| Each echo counted as a second line | -1 each |
| The count of independent lines, with its reason | +2 |
| The typology with one indicator for it, one against and the alternative | +2 |
| The confidence word with its reason | +2 |
| A High that rests on echoes | -3 |

Time only breaks ties. The points come from counting origins, and the penalties fall on counting labels.

## The typology and the confidence word

Likeliest typology: an OTC desk's address (`@chainalysis_launderingnetworks_2026`: OTC desks gather "numerous small deposits into wholesale amounts"). The flows fit: about 300 small USDT deposits from many senders, nine large transfers out to two addresses.

- One indicator for: the small many-sender deposits and the large transfers out.
- One against: some inflows are regular sweeps, which fit an exchange's hot wallet, as Vendor C reads it (`@victor_clustering_2020`; a service can sit inside an exchange's cluster, `@kappos_howpeelmillion_2022`).
- The alternative: an exchange's hot wallet.
- Confidence: Moderate. One strong line (the release) plus flows that fit but have a known false positive. High would need a second independent origin, such as an exchange's own records for the two addresses it pays. Low is defensible only for a team that treats the release itself as unverified: ask why.
- A High that rests on echoes (the label set, the story, the vendors or the freeze counted as lines) takes the -3.

The word follows `@odni_icd203_2015` (sources' quality and access; alternatives; indicators that would change the judgement) and the course scale, no percentages.

## Sources

Every claim above traces to a `Blockchain.bib` key named beside it; the as-of dates are in the lab card's Sources list.
