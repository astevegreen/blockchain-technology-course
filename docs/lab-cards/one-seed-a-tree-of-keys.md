# Design card: One seed, a tree of keys

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 4: the BIP39 lab from the expert feedback). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | One seed, a tree of keys (review idea 14, built on Ian Coleman's BIP39 tool) |
| Replaces | nothing |
| Opens from | `lessons/bitcoin/05-BF-wallet_types.qmd`, "The path names coin, account, chain and index" |
| Day | Day 2, lesson ② (wallet types, seed phrases and derivation) |
| Kind | prediction lab (five minutes) |

Which slide opens it is a question for the owner. The build spec's trial rule is "the slide whose title states
the right belief", here "One seed grows a whole tree of keys". This card proposes the path slide two slides later,
because the twist turns on the path and that is where students meet it. Day 2's lesson ① opens What time was it
sent?, so this is lesson ②'s one lab.

## The ten lines

1. **The wrong belief**: "The coins are stored in the wallet, and each address is a wallet of its own." Belief 4
   on the plan's list, marked common by the owner; review idea 14 words it "each address is a separate wallet".
2. **The prediction** (shell: `commit`): "A notebook holds twelve words. Typed into a wallet, how many Bitcoin
   addresses do they open?" Choices: one; twelve, one per word; the few the owner made when setting it up; as many
   as the wallet asks for, all from these words. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student opens the BIP39 tool from the lab, types SLIP-0014's test phrase
   ("all" twelve times) and picks the BIP84 tab. The address table fills, and its first two rows match the
   slide: bc1qannf…nfkk and bc1q7e6q…ru2m. "More rows" adds more each time it is pressed, with no end. Then the
   student swaps one word for another list word (the lab names one the checksum refuses), and the tool answers
   "Invalid mnemonic"; a misspelt word gets "not in wordlist, did you mean …?". The path, public key and private
   key columns are read last.
4. **The constraint**: a wallet hands out a fresh address for every payment and for its own change, and a backup
   made once has to cover keys that do not exist yet. So every key grows from one seed, and the seed is written as
   words a person can copy by hand; the same words give the same keys on any device.
5. **The name** (shell: `name`): HD wallet. Parts: hierarchical (a tree of branches) + deterministic (the same
   words always give the same keys). Plain: a wallet whose every key grows from one seed, so its words restore
   every address it has used or will use.
6. **The explorer view** (shell: `explorer`): bc1qannf…nfkk and bc1q7e6q…ru2m on a Bitcoin explorer, as a dated
   snapshot (the lab runs offline): two separate address pages, 14 transactions and 2, none shared, and neither
   page names the other or the words. The payments sit on the chain at the addresses; the words hold only the
   keys that spend them. Only the seed links the two, or the tool's "Account Extended Public Key" in the BIP84
   tab (the next slide's subject).
7. **The twist** (shell: `twist`): a colleague restores the same twelve words in another wallet and reports
   "first address 1JAd7…WaGL, not the bc1q… one in the case file: did you copy the words wrong?" The student
   switches the tool to its BIP44 tab, and 1JAd7…WaGL is row 0. "Why a different address?" Choices: a word was
   miscopied; the same words open different wallets at random; same words, different path: the other wallet uses
   purpose 44' (legacy addresses), not 84'; someone moved the funds. Answer: a different path. A miscopied word
   would most likely have been refused by the wallet. The words alone do not say which path the owner used, so
   check each path before calling a phrase wrong or a wallet empty.
8. **The sentence** (shell: `tell`): "The agent asks what the twelve words are and whether we now have the
   whole wallet." Example: "The twelve words are a BIP39 seed phrase, which is the wallet itself: they
   regenerate every address it has used or will use. On the native SegWit path (m/84'/0'/0') its first
   receiving address is bc1qannf…nfkk. The words do not record which path or passphrase the owner used, so the
   addresses found so far may not be the whole wallet (Low confidence that they are: two paths checked, the
   others and a passphrase untried)."
9. **The game, if any**: none. The prediction and the twist are the hook; day 2's afternoon lab plans the xpub
   game ("find a classmate's addresses from an xpub").
10. **The archetype**: step-by-step procedure.

The opening case (shell: `case`): a notebook from a suspect's desk holds twelve plain English words and nothing
else. The agent asks: "Is this a password? To what?"

Left out, for the owner to see:

- The passphrase twist (every passphrase opens a valid wallet) is not used: one twist per lab. It stays on the
  slide "A seed phrase is the whole wallet as words", and the example sentence names it.
- The lab uses only SLIP-0014's published test phrase, and says so on screen. How a phrase found in a case is
  handled is legal process, which is out of scope.

How it is built: the tool's single offline file (`bip39-standalone.html`, MIT) ships in the lab's own folder with
its licence notice, so it runs from `src.zip` with no network. The shell's `do` step opens it beside the lab,
and the student comes back to finish.

## Load check

- [x] One new term per step: HD wallet is the only term named. "Seed phrase", "path" and "purpose" come from the
  slides before; "Invalid mnemonic" and the tab names are the tool's own words.
- [x] Nothing drawn for decoration: the address rows are what the student predicts.
- [x] Labels sit on the thing they name: each path beside its address.
- [x] Objects use the shared look: `.addr` for the addresses, `.key` for the account key, `.conf` for the
  confidence word; the tool keeps its own look, since it is used as an analyst would meet it.

## Sources

The notebook and the colleague are made up for the lab and say so; the phrase and its addresses are SLIP-0014's
published test values.

- Twelve to 24 words from a 2048-word list; a 12-word phrase carries a 4-bit checksum, so about one swap in
  sixteen passes it; the words and an optional passphrase make the seed; every passphrase gives a valid wallet —
  `@palatinus_bip39mnemoniccode_2013`
- One seed derives a tree of keys, with a receiving chain and a change chain; addresses from one seed cannot
  easily be tied together on chain; an extended public key lists a branch's addresses —
  `@wuille_bip32hierarchicaldeterministic_2012`
- The coins stay on the blockchain; a wallet stores the keys that control them —
  `@yaga_blockchaintechnologyoverview_2018`
- Anyone with the words can restore the wallet on any device — `@lesavre_blockchainnetworkstoken_2021`
- Path m / purpose' / coin_type' / account' / change / address_index; purpose 44' —
  `@palatinus_bip44multiaccounthierarchy_2014`
- Purpose 84' is native SegWit; a wallet that does not support the path "will not discover accounts at all", so
  the words alone do not settle the path — `@rusnak_bip84derivationscheme_2017`;
  `@palatinus_bip39mnemoniccode_2013`
- "all" twelve times: m/84'/0'/0'/0/0 bc1qannfxke2tfd4l7vhepehpvt05y83v3qsf6nfkk, m/84'/0'/0'/0/1
  bc1q7e6qu5smalrpgqrx9k2gnf0hgjyref5p36ru2m, and under "Legacy / P2PKH / BIP44" m/44'/0'/0'/0/0
  1JAd7XCBzGudGpJQSDSfpmJhiygtLQWaGL — `@rusnak_slip0014stresstest_2015`
- The two bc1q addresses' histories: 14 transactions and 2, none shared —
  `@mempoolspace_addressbc1qannf_2026`; `@mempoolspace_addressbc1q7e6q_2026` (as of 10 Nov 2026)
- The tool: MIT licence; a standalone offline file; BIP32, BIP44, BIP49, BIP84 and BIP141 tabs, BIP44 open by
  default; "Invalid mnemonic" and "not in wordlist"; "Account Extended Public Key"; the last word holds a
  checksum; "more rows" — `@coleman_bip39tool_2026` (as of 10 Nov 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: waiting
