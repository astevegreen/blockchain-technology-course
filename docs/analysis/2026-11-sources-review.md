# Sources review (findings only)

Build Tracker row "Sources review (findings only)". Owner, 12 Nov 2026: a review of every source the course uses,
for (1) sources a course like this would be expected to cite but does not, and (2) sources it cites that are not
generally considered trustworthy. It changes nothing: every item below is a recommendation for the owner to decide.

Read 12 Nov 2026. `Blockchain.bib` holds 954 entries: 558 are cited on visible slides, 41 only on hidden slides
(`.content-hidden`), and 355 are not cited at all. Counts below are visible citations unless marked "hidden".
Lessons are named by code (04-FO is `lessons/forensics/04-FO-*.qmd`); days follow `docs/build-spec.md` "Lessons by day".

**The short version.** The base is sound. The core research (Meiklejohn, Ron and Shamir, Möser, Kappos, Victor,
Daian, Qin, Gervais), the core protocol papers (Nakamoto, Wood, Lamport, FLP, PBFT, Raft) and the core US guidance
(FinCEN 2013 and 2019, OFAC 2021, FATF 2021, ICD 203) are all cited. Four problems are worth fixing: two
misattributed sets of entries cited on visible slides, one Medium post carrying three PoS slides, and two entries
whose links cannot reach the source. The biggest gap is that days 6 to 9 cite almost none of the peer-reviewed
measurement studies of ransomware, darknet markets, mixers, Monero and DeFi attacks that the field treats as standard.

## Part 1. Cited sources that are wrong or weak

### 1a. Misattributed or unreachable (fix: the slide's claim is fine, the entry is not)

| # | Entry | Cited in | Problem | Fix |
|---|---|---|---|---|
| A1 | `vogels_eightfallaciesdistributed_1997` | 01-DS ×11 | Author given as Werner Vogels. The Eight Fallacies are L Peter Deutsch's list (Sun, 1994), with the eighth added by James Gosling (c. 1997). The URL is Arnon Rotem-Gal-Oz's paper "Fallacies of Distributed Computing Explained", a secondary write-up. | Re-author as Deutsch (and Gosling), or cite Rotem-Gal-Oz's paper under his own name. |
| A2 | `boneh_*_2020` (17 entries) | `boneh_hashfunctions_2020`: 01-CM ×2, 02-CP ×6, 03-CP ×2, 04-CP ×3 (hidden ×9); policy/CBDCs: 02-AS ×3; quantum: 04-AS, 05-AS; FHE and ZKP: 04-DS | Author given as Boneh and Shoup ("A Graduate Course in Applied Cryptography"), but every URL is intensecrypto.org or files.boazbarak.org: Boaz Barak's lecture notes "An Intensive Introduction to Cryptography" (Harvard CS 127). `boneh_graduatecourseapplied_2020` links to `intensecrypto.org/public/.html`, a page that does not exist. | Re-author as Barak, retitle to the notes' real chapter names; or, where the slide wants Boneh and Shoup, cite their book (toc.cryptobook.us). |
| A3 | `u.c.f.library_digitalwalletsoverview_2022` | 01-AS ×3, 05-AS ×1 | Author "U. C. F. Library"; the URL is `stars.library.ucf.edu/cgi/viewcontent.cgi` with no query string, so it points at no document. Probably a student paper in a repository; it cannot be checked. | Replace with `bitcoin.orgdevelopers_walletsdeveloperguide_2024` (already cited beside it) or Mastering Bitcoin's wallets chapter. |
| A4 | `diffie_newdirectionscryptography_1976` | 01-CP ×1 (hidden ×7) | URL runs through a university library proxy (`…idm.oclc.org`), which students cannot open. | Use the DOI, 10.1109/TIT.1976.1055638. |
| A5 | `l00_policyreview_trust_blockchain_2021`, `l00_iacis_public_perceptions_2022` | uncited / hidden ×1 | Journal or organisation name entered as the author. | Fix the author fields if either is cited again. |

Checked and fine: `l2beat_stages_2026` (08-EF ×2) links to ethbeat.org, labelled "ETHBEAT (formerly L2BEAT)". That
looked like a wrong domain, but L2BEAT did rebrand as ETHBEAT in 2026 (Crypto Briefing). The other entry,
`l2beat_l2beat_2025`, still uses l2beat.com, which also still resolves.

### 1b. Weak sources carrying a claim on a visible slide

| # | Entry | Cited in | Why weak | Better source |
|---|---|---|---|---|
| W1 | `namoo908_ethereumbeaconchain_2025` (Medium post) | 03-CM ×3: epochs, checkpoints, justification | A personal blog post supports a protocol fact, next to ethereum.org. | The consensus specs or Casper FFG (Buterin and Griffith 2017) and Gasper (Buterin et al. 2020); or `offchain_ethereumbeaconchain_2023`, already in the bib (02-EF ×2). |
| W2 | `ammous_bitcoinstandarddecentralized_2018` | 04-IN ×5: the money-history, central-bank and "Austrian vs. Keynesian" slides | An advocacy book, not scholarship. Fine as "what Bitcoin's advocates argue"; weak as a neutral source for monetary history. | Keep it, labelled as the advocates' case, and pair the history slides with the BIS and Federal Reserve sources already on 04-IN. |
| W3 | `salisu_blockchainforensicsmodern_2023` (ICCWS paper) | 08-EF ×4 (wrapped Monero, atomic swaps), 01-FO ×1; hidden ×12 | A broad survey from a small conference, used for specific technical claims. | A primary source per mechanism, found with the `source` skill; for wrapped assets, the bridge sources already staged for day 8. |
| W4 | `hammi_nonfungibletokensreview_2023`, `ante_nonfungibletokennft_2022` (IEEE IoT Magazine; MDPI FinTech) | 06-EF ×3 and ×2 | General reviews in venues outside the field's core. Acceptable, not strong. | Das et al. 2022 (CCS) and Wang et al.'s SoK on tokenization (already in the bib) for the security points. |
| W5 | `atlam_blockchainforensicssystematic_2024` (MDPI) | 01-FO ×1; hidden ×5 | MDPI review; one visible use. | Low priority; pair with a measurement paper from Part 2. |
| W6 | `pishdar_denialofserviceattackspermissioned_2025` (MDPI) | 02-PC ×2 | As above, for Fabric DoS. | Low priority; Hyperledger's own docs or Androulaki et al. (already cited). |
| W7 | `sendin_detectingcoldstorage_2018` (single-author, Brazilian national symposium) | 04-FO ×13, 05-BF ×2 | Peer reviewed and specific, but it carries the whole sweep slide set alone. | Keep it. 04-FO already pairs it with Victor 2020 (`victor_clustering_2020`, ×23) for Ethereum; Sendin alone covers the Bitcoin sweep details. Low priority. |
| W8 | `decrypt_dprk2025theft_2025` | 13-FO ×4 | Trade press restating Chainalysis's figure. | Cite the Chainalysis report directly (the 2026 Crypto Crime Report entry) or the MSMT report (C1). |
| W9 | Reuters stories through republishers: `l34_euronews_reuters_terra_2022`, `l34_aljazeera_reuters_ftx_bankruptcy_2022`, `l33_euronews_reuters_china_…_2022`, `l33_marketscreener_reuters_…digital_euro_…_2025` | 05-AS, 05-EF ×2, 03-AS | Third-party copies of wire stories. | Cite reuters.com, or the primary record (the Terra and FTX court filings, the Council of the EU press release). |
| W10 | `hristov_ethereumvalidatorslost_2025` (BeInCrypto) | 02-EF ×1 | Crypto trade blog for a validator-count fact. | beaconcha.in or the client-diversity dashboard already cited. |
| W11 | `lovejoy_bitcoingoldbtg_2020` (GitHub gist) | 04-BF ×2 | A gist, for the Bitcoin Gold 51% attack. | Keep only if the gist is the attack's primary analysis; otherwise a primary analysis found with the `source` skill. |
| W12 | `l34_bitcoin_wiki_quantum_2026` (Bitcoin Wiki) | 04-CP ×1 | An editable wiki. | NIST's post-quantum standards (FIPS 203–205), or the relevant BIP if the slide is about Bitcoin's plans. |

Acceptable, with the caveat already on the slide or easy to add: victims' own incident reports (Bitget, Ronin,
Binance), which are primary accounts and already paired; the CipherTrace Monero press release, which 02-FO frames as
a vendor claim; Russian state media (`l33_tass_…`, 03-AS ×1), usable only as Russia's stated position; CoinDesk and
The Block for event reporting.

### 1c. Homepage-only citations (25 entries cited visibly)

A citation to a site's front page cannot support a specific claim: a reader cannot find the sentence it backs.
Most sit in the day-3 conclusion lessons (01-AS, 03-AS, 05-AS), on "where to read more" slides:
`chainalysis_reports_2025` (01-AS ×5, 05-AS ×3, 05-EF ×2, 03-AS, plus five 02-FO notes), `sec_sec_2025`,
`ftc_cryptocurrency_2025`, `fbi_ic3_2025`, `federalreserve_federalreserve_2025`, `coindesk_coindesk_2025`,
`theblock_theblock_2025`, `messari_research_2025`, `rekt_rektnews_2026`, `crs_crsreports_2025`, `binanceus_home_2026`
and `l2beat_l2beat_2025` (also 08-EF's rollup examples table).
On a resources slide that is fine. Where it backs a fact (for example 02-FO's notes and 05-AS's trend claims),
it should be the specific report. Dashboards whose front page is the data (bitnodes.io, mevwatch.info,
clientdiversity.org, 4byte.directory) are fine as they are.

### 1d. Metadata hygiene

- 42 cited `online` entries have no `urldate` (the date the page was read), mostly the `l33_` batch behind the
  conclusion and geopolitics lessons. Pages change; the read date is what makes the citation checkable.
- `antonopoulos_masteringbitcoinprogramming_2017` (the 2nd edition) is the course's most-cited book: 82 visible
  citations across 12 lessons. A 3rd edition by Antonopoulos and Harding came out in Nov–Dec 2023 (O'Reilly), free
  to read on GitHub under CC BY-NC-ND 4.0, and updated for Bitcoin as of 2023.

## Part 2. Sources a course like this would be expected to cite

### 2a. Already in the bib, not cited

| # | Entry | Where it belongs |
|---|---|---|
| C1 | `msmt_dprkcyber_2025`: the Multilateral Sanctions Monitoring Team's DPRK cyber report (22 Oct 2025) | D9 ① North Korea (13-FO); the successor to the UN Panel of Experts |
| C2 | `l33_united_nations_un_panel_of_experts_dprk_reports_2025` | D9 ①, for the 2019–2024 history |
| C3 | `harrigan_unreasonableeffectivenessaddress_2016` | D6 clustering (02-FO): why the multi-input heuristic works so well |
| C4 | `elliptic_crosschaincrime_2025`, `trmlabs_bybitupdate_2025` | Day 8's bridge slides, as staged in `2026-11-bridge-tracing-sources.md` |
| C5 | `l34_fatf_virtual_assets_guidance_2026` | D5 rules (05-FO) |
| C6 | Prince Group entries (`govuk_princegroup_2025`, `ustreasury_princegroup_2025`, `ustreasury_princegroup_2026`, `usdoj_chenzhiindicted_2025`) | Day 10's trace lab; expected to stay uncited by lessons |

### 2b. Not in the bib

Each was checked to exist in this review unless marked "known, not re-checked" (standard works whose details
the `source` skill should confirm when one is added).

**Day 6: clustering and ransomware**

| # | Work | Why expected |
|---|---|---|
| M1 | Huang et al., "Tracking Ransomware End-to-end", IEEE S&P 2018 | The standard end-to-end measurement of ransomware payments and cash-out (BTC-e). |
| M2 | Paquet-Clouston, Haslhofer and Dupont, "Ransomware payments in the Bitcoin ecosystem", *Journal of Cybersecurity* 5(1), 2019 | The method for finding ransom payments on-chain; shows the market is concentrated in a few operators. |
| M3 | Reid and Harrigan, "An Analysis of Anonymity in the Bitcoin System", 2011 (known, not re-checked) | The first clustering paper; precedes Meiklejohn. |
| M4 | Androulaki et al., "Evaluating User Privacy in Bitcoin", FC 2013 (known, not re-checked) | Early change-address and behaviour-based clustering. |
| M5 | Kalodner et al., "BlockSci", USENIX Security 2020 (known, not re-checked) | The open-source analysis platform; fits the open-source-tools rule. |
| M6 | Christin, "Traveling the Silk Road", WWW 2013; Soska and Christin, USENIX Security 2015 (known, not re-checked) | The standard darknet-market measurements; Silk Road is taught in 01-BF, 01-FO, 02-FO and 03-FO from DOJ releases alone. |
| M7 | Foley, Karlsen and Putniņš, "Sex, Drugs, and Bitcoin", *Review of Financial Studies* 2019 (known, not re-checked) | The most-cited estimate of illicit share; often quoted, so analysts need to know its method. |

**Day 7: mixers, privacy coins, cryptojacking**

| # | Work | Why expected |
|---|---|---|
| M8 | Kumar, Fischer, Tople and Saxena, "A Traceability Analysis of Monero's Blockchain", ESORICS 2017 | The companion to Möser 2018 (cited); found the real input in about 87–88% of early rings. |
| M9 | Möser, Böhme and Breuker, "An inquiry into money laundering tools in the Bitcoin ecosystem", eCrime 2013 (known, not re-checked) | The first test of mixing services. |
| M10 | Konoth et al., "MineSweeper", CCS 2018 | The standard study of in-browser cryptojacking; pairs with Pastrana (cited). |

**Day 8: drainers, flash loans, contracts, NFT wash trading**

| # | Work | Why expected |
|---|---|---|
| M11 | Zhou et al., "SoK: Decentralized Finance (DeFi) Attacks", IEEE S&P 2023 | The standard taxonomy of DeFi attacks: 181 incidents, oracle attacks the most common. |
| M12 | Atzei, Bartoletti and Cimoli, "A Survey of Attacks on Ethereum Smart Contracts", POST 2017 (known, not re-checked) | The classic contract-bug taxonomy behind reentrancy and its kin. |
| M13 | Das et al., "Understanding Security Issues in the NFT Ecosystem", CCS 2022 | Measures wash trading and marketplace flaws; would also replace W4. |
| M14 | Cong, Li, Tang and Yang, "Crypto Wash Trading", *Management Science* 69(11), 2023 | The standard test for fake exchange volume (over 70% on unregulated exchanges). |

**Days 2 to 4: protocols**

| # | Work | Why expected |
|---|---|---|
| M15 | Buterin and Griffith, "Casper the Friendly Finality Gadget", 2017; Buterin et al., "Combining GHOST and Casper" (Gasper), 2020 (known, not re-checked) | The primary sources for Ethereum's finality; would replace W1. |
| M16 | Gudgeon et al., "SoK: Layer-Two Blockchain Protocols", FC 2020 (known, not re-checked) | The standard L2 survey for day 4. |
| M17 | Poon and Dryja, "The Bitcoin Lightning Network", 2016 (known, not re-checked) | 03-BF teaches Lightning with no primary source. |

**Days 5 and 9: rules, typologies, East and Southeast Asia**

| # | Work | Why expected |
|---|---|---|
| M18 | US Treasury, "Illicit Finance Risk Assessment of Decentralized Finance", 6 Apr 2023 | The US government's own DeFi risk statement; names ransomware, scams, stolen-asset laundering and DPRK. |
| M19 | US Treasury, National Money Laundering Risk Assessment 2024 (known, not re-checked) | The government framing for typologies (12-FO). |
| M20 | FATF, "Virtual Assets Red Flag Indicators of ML/TF", Sep 2020 (known, not re-checked) | The standard red-flag list; fits D9 ② typologies. |
| M21 | FBI, CISA and Treasury, AA22-108A "TraderTraitor", 18 Apr 2022 | The joint advisory naming the DPRK group behind later exchange thefts. The bib quotes "TraderTraitor" inside another entry but does not cite the advisory. |
| M22 | UNODC, "Casinos, Money Laundering, Underground Banking, and Transnational Organized Crime in East and Southeast Asia", 15 Jan 2024 | The UN's account of the scam-compound economy behind Huione and Prince Group (05-FO, day 10). |
| M23 | Griffin and Mei, "How Do Crypto Flows Finance Slavery? The Economics of Pig Butchering", SSRN, Feb 2024 | The main academic trace of pig-butchering flows. Tether disputes it, so cite it with that noted. |

**Day 9 ③: analytic tradecraft**

| # | Work | Why expected |
|---|---|---|
| M24 | Sherman Kent, "Words of Estimative Probability", 1964 (known, not re-checked) | The origin of the confidence words ICD 203 standardizes. |
| M25 | Heuer, *Psychology of Intelligence Analysis*, CIA 1999; CIA, *A Tradecraft Primer*, 2009 (known, not re-checked) | The standard texts on bias and structured techniques (Analysis of Competing Hypotheses). No lesson cites either. |

## Part 3. Recommendations for the owner

Each item is separate; approve, change or drop any of them.

| # | Recommendation | Size |
|---|---|---|
| R1 | Correct the misattributed and unreachable entries A1–A4 (bib edits; slide text unchanged). | S |
| R2 | Replace the Medium post W1 with the consensus specs or Casper FFG/Gasper (M15). | S |
| R3 | Replace or pair the weak sources W3, W8–W12 as listed; leave W2 (Ammous) cited but labelled as the advocates' case. | S–M |
| R4 | Swap homepage citations that back a specific fact for the specific report (1c); leave resources slides alone. | M |
| R5 | Add `urldate` to the 42 cited pages that lack one (1d). | S |
| R6 | Move the Bitcoin citations to Mastering Bitcoin 3rd edition (2023), re-checking each cited page. | M |
| R7 | Cite C1 and C2 (MSMT, UN Panel) when D9 ① is built; C3 on day 6. | with that day's build |
| R8 | Add M1–M25 to each day's build as that day is reworked, through the `source` skill, rather than as one sweep. | with each day |

R1, R2 and R5 are mechanical and could be one Sonnet build item. R3, R4 and R6 change which source stands behind a
slide, so each slide needs a re-read. R7 and R8 are content additions that belong to the day builds.
