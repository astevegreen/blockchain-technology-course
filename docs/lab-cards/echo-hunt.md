# Design card: Echo hunt

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6: day 9's sources exercise, built as the echo hunt). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Echo hunt (day 9's sources exercise, new; the lab plan's "Every lab" row for day 9) |
| Replaces | nothing |
| Opens from | `lessons/forensics/14-FO-fusing_sources.qmd`, "An echo is not a second line" |
| Day | Day 9, afternoon, last: after the Tron trace's graded note, before day 10's test |
| Kind | game (teams of three or four, one page per team, about 40 minutes) |

Teams get one invented Tron address, T-echo, and seven source cards about it that partly disagree; an eighth
arrives as the twist. Each card shows what it says, its date and its stated basis. Teams trace every card to where
its claim came from, count the independent lines, pick the likeliest typology and give a confidence word. It is
practice: day 9's graded point stays the Tron trace's note. It grows the lesson's practice slide (T-practice:
two vendor tags, a freeze, a listing) by a disagreeing source, the address's own flows and a typology.

## The ten lines

1. **The wrong belief**: "Five sources that say the same thing are five reasons to be sure." It is not on the
   plan's list of fifteen; its nearest is belief 14 (a tool's label or a sanctions listing is proof), which the
   cards also test.
2. **The prediction** (shell: `commit`): "Five of the seven cards name T-echo as Desk X's address. How many
   independent lines of evidence do they make, and how do you tell?" Choices: (a) five: five sources agree; (b)
   four: the news story only reports; (c) one per origin: trace each card to where its claim came from; (d) one:
   only the government's word counts. Then High, Moderate or Low.
3. **The action** (shell: `do`): the team drags each card onto the card it came from, or onto "the chain" or
   "basis unknown", and the page stacks them. The label set's basis is OFAC's list; the news story quotes the
   release; Vendor B's source field names Vendor A; Vendor A states no basis and first tags T-echo the day after
   the release. A team that picked (a) ends with three of the five on the release and Vendor B on Vendor A in
   "basis unknown": one line for certain, and one unverified label at most, Low, which may itself echo the
   release. The count of five falls in front of them. Across all seven cards two origins are known: the release,
   and the address's own flows, which the team's flow summary and Vendor C both read.
4. **The constraint**: labels get copied. An open label set is built from OFAC's list; a vendor's clustering
   draws on "data leaks, court documents, and data partnerships"; a news story quotes the release. A copy carries
   its origin's errors and adds no evidence, so counting copies turns one source into a false High. ICD 203 asks
   analysts to describe each source's quality and access, which means knowing where each claim came from.
5. **The name** (shell: `name`): echo. Plain: a source that agrees with another only because it copied it, so
   the two are one line. Count the origins, not the labels.
6. **The explorer view** (shell: `explorer`): the day 9 query page, query 6, on the address the team just traced:
   USDT's `AddedBlackList` event for TDxZ1X… at 16:14 UTC on 30 Sep 2026, with OFAC's listing of the same day in
   its "what a source says" column. Two records, one on chain and one off, the same day: the freeze is a fact,
   but it may be a response to the listing itself, so an echo can cross kinds, not only run between vendors.
7. **The twist** (shell: `twist`): a new card: "USDT's contract blacklisted T-echo two hours after the release;
   Tether says it acted in coordination with OFAC." "Does the freeze move the confidence word?" Choices: yes, to
   High: an on-chain record now agrees; yes, because issuers check their own customers; no: the freeze is a fact,
   but its reason is what the issuer says, and here that is the release; no, freezes are never evidence. Answer:
   no, it echoes the release. A freeze for a reason of its own (say, the issuer's own fraud reports) would be a
   second origin.
8. **The sentence** (shell: `tell`): "Tell the agent what T-echo is, and how sure we are." Example: "Treasury
   designated Desk X, an OTC desk, on 3 Mar and listed T-echo as its address. Our eight sources come down to two
   origins: that release, which the label set, the news story, the freeze and Vendors A and B repeat or may
   repeat, and the address's own flows. The flows fit an OTC desk: about 300 small USDT deposits from many
   senders, and nine large transfers out to two addresses. Some inflows are regular sweeps, which also fits an
   exchange's hot wallet, as Vendor C reads it. We assess with Moderate confidence that T-echo is an OTC desk's
   address; an exchange's records for the two addresses it pays would raise or lower that."
9. **The game, if any**: echo hunt (owner, 10 Nov 2026). Each card traced to its origin with its reason: +1
   (eight cards). Each echo counted as a second line: -1. The count of independent lines with its reason: +2. The
   typology with one indicator for it, one against and the alternative: +2. The confidence word with its reason:
   +2. A High that rests on echoes: -3. Time only breaks ties. The points come from counting origins, and the
   penalties fall on counting labels, so the score is the concept.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): a colleague pastes seven tabs into the case file about one Tron address and
writes: "Five sources say it's Desk X. That's High, surely. Can we send it?"

The cards (all invented, and the page says so): (1) Treasury's release, 3 Mar, designating Desk X and listing
T-echo; (2) an open label set's tag, basis "OFAC's SDN list"; (3) a news story, 4 Mar, quoting the release; (4)
Vendor A's tag "Desk X OTC", first seen 4 Mar, basis not stated; (5) Vendor B's tag, source field "Vendor A"; (6)
the team's flow summary of T-echo; (7) Vendor C's tag "exchange hot wallet", basis "receives sweeps from deposit
addresses". The twist adds (8), the freeze.

Left out, for the owner to see:

- The real day 9 address (TDxZ1X…, OFAC-listed 30 Sep 2026) is not the hunt's case: the team has just graded it,
  so its answer is known. It appears only in the explorer view.
- Vendor A's unknown basis scores either reason: "basis unknown, so one unverified label, Low, not a second line",
  or "dated after the release, so likely an echo". Both are the lesson's.

How it is built: one folder, `blockchain-course/assets/labs/echo-hunt/`, on the shared shell and look, offline;
the `do` step is the stacking board, which records the team's stacks and holds no key. The scoring key (each
card's origin and the accepted reasons) goes in `quizes/`, which students never receive.

## Load check

- [x] One new term per step: echo is the only term named; "line", "origin", "typology" and the confidence words
  come from days 5 to 9.
- [x] Nothing drawn for decoration: the cards and their stacks are the count.
- [x] Labels sit on the thing they name: each card's date and basis on the card.
- [x] Objects use the shared look: `.addr` for T-echo, `.conf` for the confidence word; the cards and stacks need
  one new object in `look.css`, added when the lab is built.

## Sources

T-echo, Desk X, the vendors, the news story, the dates and the flows are made up for the game and say so.

- Count the origins, not the labels; three tags from one government release are one strong line, Moderate; a tag
  of unknown origin is one unverified label, Low — `lessons/forensics/14-FO-fusing_sources.qmd`;
  `@odni_icd203_2015`
- An open label set built from OFAC's SDN list, covering TRX and USDT — `@b10c_ofacaddresses_2026` (as of
  1 Nov 2026)
- A vendor's clustering uses "data leaks, court documents, and data partnerships" — `@sterlingov_cadc_2026`
- Source quality, access and validation; alternative hypotheses; indicators that would change the judgement —
  `@odni_icd203_2015`
- OTC desks gather "numerous small deposits into wholesale amounts" — `@chainalysis_launderingnetworks_2026`
- Deposit addresses sweep into an exchange's hot wallet — `@victor_clustering_2020`; a service can sit inside an
  exchange's cluster — `@kappos_howpeelmillion_2022`
- USDT on Tron can blacklist an address (`addBlackList`, event `AddedBlackList`) — `@tether_usdttroncontract_2026`
  (as of 31 Oct 2026); Tether freezes in coordination with OFAC — `@tether_freeze344m_2026`
- TDxZ1X… listed by OFAC on 30 Sep 2026, and blacklisted by USDT at 16:14 UTC that day —
  `@ofac_trendearagua_2026` (read 1 Nov 2026); the day 9 snapshot, `dynamic-labs/tron/snapshot/d9/` (java-tron
  4.8.2.4, read 1 Nov 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: selected "Bitcoin trace decoys", "Echo hunt", "Name the money and the flaw" (10 Nov 2026)
