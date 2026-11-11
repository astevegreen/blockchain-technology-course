# Design card: The wallet that emptied itself

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | The wallet that emptied itself (review idea 5) |
| Replaces | nothing (new; the one idea kept from the retired symmetric labs: keys come from randomness) |
| Opens from | `lessons/forensics/09-FO-approvals_drainers_poisoning.qmd`, "Ronin: stolen keys, not broken code", recalling day 1 ②'s "Keys fail through people and bad randomness" (`lessons/primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd`) |
| Day | Day 8, lesson ① (approvals, drainers and poisoning) |
| Kind | prediction lab (five minutes) |

Placement: day 8 ① (owner, 11 Nov 2026: "Approve, day 8 ① (Recommended)"). Day 1 ② already opens Forge the payment, and day 1 opens one lab per lesson
(commit 9161452). Day 8 ① has no prediction lab, and it is the lesson where analysts explain thefts.

## The ten lines

1. **The wrong belief**: "The wallet was emptied and the owner never shared the key, so the thief must have broken
   the cryptography." Belief 15 on the plan's list ("a hack means the cryptography was broken"), marked common by
   the owner, in its key form; "Name the money and the flaw" keeps its contract form.
2. **The prediction** (shell: `commit`): "Ben made his wallet offline with a command-line tool, wrote down nothing
   anyone could see, and clicked no links. Last night every coin left it, in a payment with a valid signature from
   his own address. How?" Choices: (a) the thief worked out Ben's private key from his public key; (b) the thief
   forged Ben's signature; (c) the thief made the same key Ben's tool made, by trying every number the tool could
   start from; (d) Ben sent it himself and forgot. Then High, Moderate or Low.
3. **The action** (shell: `do`): on the instructor's count, every student presses "Make a wallet" on the lab's
   wallet maker, a made-up tool that, like Milk Sad's `bx`, starts its random numbers from the clock, here to the
   second. Students who pressed in the same second get the same address, and so the same key: the class sees it
   on screen. Then the student gets Ben's address and one fact, that he made it yesterday with this tool. The page
   tries every second of yesterday, 86,400 starting numbers, and finds Ben's key in moments; the student signs a
   payment from his address, and the signature checks. Answers (a) and (b) fail in front of them: the curve was
   never touched, and the signature is real. The seed and the key's hex appear last.
4. **The constraint**: a private key is one number out of about 2^256, too many to try; a key made from a starting
   number that can take only 2^32 values (Milk Sad's `bx`) or 86,400 (this lab's tool) is one of that many, and an
   attacker can try them all. The curve holds; the randomness that picks the key is the weak point, so a wallet
   must start from enough unpredictable bits (BIP 39 asks for 128 to 256).
5. **The name** (shell: `name`): brute force. Plain: trying every possible value until one fits. It fails against
   a real key and wins against a key drawn from a small set.
6. **The explorer view** (shell: `explorer`): Ben's outflow as an Ethereum explorer's transaction page shows it
   (the same view Forge the payment opened on day 1): From is Ben's address, worked out from the signature, with
   its nonce, value and v, r and s. Nothing on the page marks it as theft: it is day 8's stolen-key pattern ("Five
   ways out of a wallet look different"), an outflow sent by the victim's own address with nothing on chain
   before it.
7. **The twist** (shell: `twist`): Ana's wallet is emptied the same way, but she made it with a wallet that follows
   BIP 39's 128 bits. The page runs the same search over yesterday and finds nothing. "What do you write now?"
   Choices: the thief broke the cryptography after all; the key was copied or taken some other way, as Ronin's
   were (phishing, malware, a photographed seed phrase); the network moved the coins; Ana is lying. Answer: the
   second. A failed search rules out one cause, not the key's theft; on chain a thief's spend and an owner's spend
   look the same, so who signed needs other evidence.
8. **The sentence** (shell: `tell`): "The agent asks how Ben's wallet was emptied." Example: "The payment that
   emptied Ben's wallet was signed with the key that controls his address (High confidence: the signature
   verifies). The tool Ben used could make only 86,400 keys that day, and we recreated his from his address alone,
   so the thief most likely did the same (Moderate confidence). Nothing shows that the cryptography was broken."
9. **The game, if any**: none. The class collision in step 3 is the hook; nothing is scored.
10. **The archetype**: simulation.

The opening case (shell: `case`): an agent forwards a victim's report: "My wallet emptied overnight. I made it
offline, I never typed my words into anything, and I never clicked a link. The thief must have cracked the
encryption. Can you prove it?" The payment's hash is attached.

Left out, for the owner to see:

- Nonce reuse (two signatures that share a number give up the private key; review idea 5's second half) is left
  out: it does not fit in five minutes beside the search, and Forge the payment leaves the PlayStation 3 case on
  day 1 ②'s slide "A signature binds the key to these exact bytes". One twist per lab.
- Placement alternatives: (1) the primer or day 1's evening work, where it stands beside the slide it recalls;
  (2) a second lab on day 1 ②, from "Keys fail through people and bad randomness", which breaks the one-lab-per-
  lesson rule of commit 9161452. Day 8 ① is recommended: it has no prediction lab, and its students are already
  explaining thefts to agents.
- Milk Sad's real drained addresses are not shown: no source in the bibliography lists them, and the lab's point
  is the mechanism.

How it is built: the wallet maker is in-house: a small generator started from the clock's second, feeding the
same vendored open-source secp256k1 library as Forge the payment, so a seed gives a real key and a real address,
offline from `src.zip`. Ben's and Ana's wallets are made at build and their seeds kept in the lab's answer key.
The page states that the tool and both victims are made up; only Milk Sad's numbers are real.

## Load check

- [x] One new term per step: brute force is the only term named; "private key", "signature", "address" and
  "nonce" come from day 1, and "seed phrase" from the wallets lesson.
- [x] Nothing drawn for decoration: the matching addresses light up only when two students' wallets match, and the
  search's counter moves only while it tries seeds.
- [x] Labels sit on the thing they name: the starting second under each wallet, the signer under the signature.
- [x] Objects use the shared look: `.key` for the keys, `.addr` for the addresses, `.sig` for the signature,
  `.hash` for the payment, `.conf` for the confidence word.

## Sources

Ben, Ana, the wallet maker, its clock seed and both thefts are made up for the lab and say so; Milk Sad's figures
and Ronin's are real.

- No one has broken secp256k1; keys are lost when they are guessable, copied or taken; a stolen key keeps working —
  the slide "Keys fail through people and bad randomness", from `@l35_milksad_update2_2023`;
  `@departmentofjustice_bitfinexhackerwife_2023`
- Libbitcoin Explorer's `bx seed` drew wallet entropy from the MT19937 Mersenne Twister seeded with 32 bits of
  system time, so every seed could be tried; versions 3.0.0 to 3.6.0, CVE-2023-39910; funds were stolen —
  `@milksadteam_milksaddisclosure_2023` (read 10 Nov 2026);
  `@l35_milksad_update2_2023`
- A private key is a number chosen at random from about 2^256 values — `@antonopoulos_masteringbitcoinprogramming_2017`
- A BIP 39 wallet starts from 128 to 256 bits of entropy — `@palatinus_bip39mnemoniccode_2013`
- Ethereum works out the sender from the signature (v, r, s) — `@wood_ethereumsecuredecentralised_2016`
- Ronin: five of nine validator keys, taken through spear-phishing and an allowlist never revoked; the
  withdrawals were valid on chain — `@roninnetwork_backtobuilding_2022`; `@roninnetwork_roninblogcommunity_2022`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale). 2^32 is about 4.3 billion and a
  day has 86,400 seconds: arithmetic, not a sourced fact.

## Approval

- Owner: "Approve, day 8 ① (Recommended)" (11 Nov 2026): opens on day 8 lesson ①, approvals, drainers and poisoning
- Built in f4c34be5 (11 Nov 2026).
