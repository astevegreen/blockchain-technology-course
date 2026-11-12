# Design card: Forge the payment

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Forge the payment (review idea 4) |
| Replaces | `signatures` (rebuilt as a prediction lab, not retired) |
| Opens from | `lessons/primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd`, "A signature authorizes; it doesn't identify" |
| Day | Day 1, lesson ② (keys, signatures and addresses) |
| Kind | prediction lab (five minutes) |

Day 1 holds more planned labs than it has room for; where this one sits is settled when day 1's labs are placed
(owner, 10 Nov: "Settle it later").

## The ten lines

1. **The wrong belief**: "A signature shows who sent it: if Ana's signature is on the payment, Ana sent it."
   Belief 5 on the plan's list, marked common by the owner.
2. **The prediction** (shell: `commit`): "This small ledger accepts any payment whose signature checks; it keeps
   no other record yet. You hold a copy of Ana's signed payment, 'Pay Ben 0.30 coins', and a key of your own. Can
   you make the ledger move Ana's money?" Choices: (a) yes: change the payee to you, and her
   signature still checks; (b) yes: sign a payment from Ana's account with your own key; (c) no: without Ana's
   private key nothing moves her money; (d) you cannot pay yourself, but you can move her money anyway. Then
   High, Moderate or Low.
3. **The action** (shell: `do`): the student tries each forgery on a small ledger that accepts any payment whose
   signature checks. Changing "Ben" to their own name, or 0.30 to 3.00, turns the check red: the signature fits
   only the bytes Ana signed. Pasting her signature onto a new message fails the same way. Signing "Pay me 0.30
   from Ana" with their own key gives a valid signature, but the ledger works out the signer as the student's
   own, empty account and refuses it. Then the student sends Ana's payment again, byte for byte: it is accepted,
   Ben is paid twice and Ana is down 0.60. Answer (d): the student never held Ana's key and still moved her money,
   so whoever sends a signed payment need not be its signer. The signature values and field names appear last.
4. **The constraint**: a copy has the same bytes and the same signature, so no signature check can tell it from
   the first send. So each payment carries the sender's counter, the account nonce from lesson ①, and the ledger
   accepts each number once: the lab's ledger gains the counter, and the copy is now refused. On Bitcoin a copy
   fails for another reason: the coin it spends is already spent, once and whole (Make change).
5. **The name** (shell: `name`): replay. Plain: sending a copy of someone else's signed payment again so that it
   runs a second time; the signature still checks, because nothing in it changed. The counter is what stops it.
6. **The explorer view** (shell: `explorer`): with the counter added, the ledger works as Ethereum does, and Ana's
   payment appears as an Ethereum explorer's transaction page shows it: From, To, Value, Nonce, and the
   signature's v, r and s. From is not a box Ana filled in: the explorer worked it out from the signature (the next slide, "Ethereum works out the sender from the
   signature"). The nonce is the field that made the copy fail.
7. **The twist** (shell: `twist`): the next day a new payment leaves Ana's account to an address no one knows,
   with a valid signature and the next counter. Ana says she did not send it. Then the case file adds one fact:
   Ana's address is 0xf4dd…08fe, the address of this lesson's worked key, whose private key is printed in
   *Mastering Bitcoin*. "What does the valid signature prove?" Choices: Ana sent it; Ana is lying; the key behind
   Ana's address signed it, and anyone who read the book holds that key; the signature is forged. Answer: the
   third. A valid signature proves the key signed, not who held it; a key can also be stolen, shared or held by a
   service.
8. **The sentence** (shell: `tell`): "The agent asks whether Ana sent the second payment." Example: "The second
   payment was signed with the key that controls Ana's address, 0xf4dd…08fe (High confidence: the signature
   verifies and the ledger accepted it). That key is printed in a published book, so the signature does not show
   that Ana sent the payment; who signed it needs other evidence."
9. **The game, if any**: none. The plan's "the lab is the game: can anyone forge it?" is the prediction itself:
   the forging attempts are the hook, scored by nothing. It is not one of the eight games the owner locked in.
10. **The archetype**: simulation.

The opening case (shell: `case`): Ana paid Ben 0.30 coins this morning. Every node on the network saw her signed
payment, and so did you. You have your own key and an empty account. The challenge on screen: make Ana's money
move.

Left out, for the owner to see:

- Nonce reuse (the PlayStation 3 key) stays on the slide "A signature binds the key to these exact bytes"; the old
  lab hid it behind `?full`. One twist per lab.
- The old lab's P-256, Ed25519 and RSA, its fake address, its curve plot and its MathJax are dropped (review
  idea 4). Cross-chain replay (the chain ID) is day 4's (03-EF) and is not shown here.

How it is built: the page signs and checks with a vendored open-source secp256k1 library, chosen at build, with
its licence notice in the lab's folder, so it runs offline from `src.zip`. Ana's and the student's keys are made
fresh in the browser; only the twist uses the published book key.

## Load check

- [x] One new term per step: replay is the only term named. "Signature", "private key" and "nonce" come from
  the slides before; "valid" and "refused" are the ledger's labels.
- [x] Nothing drawn for decoration: the check turns red or green, and the balances move, only when the ledger
  decides.
- [x] Labels sit on the thing they name: the signer under each signature, the counter on each payment.
- [x] Objects use the shared look: `.key` for the keys, `.sig` for each signature, `.addr` for the accounts,
  `.hash` for the payment's hash, `.conf` for the confidence word.

## Sources

Ana, Ben and their payments are made up for the lab and say so; the twist's address and key are the lesson's
worked example from *Mastering Bitcoin*.

- A signature is made with the private key over the transaction's hash; anyone checks it with the public key;
  change one byte and it fails — `@schmid_ecdsaapplicationimplementation_2015`;
  `@antonopoulos_masteringbitcoin3e_2023` (ch. 8)
- A signature authorizes, it does not identify: a key can be stolen, shared or held by a service; "signed with
  the key controlling address X" — the lesson's slide, from `@nakamoto_bitcoinpeertopeerelectronic_2008`;
  `@meiklejohn_fistfulbitcoinscharacterizing_2013`
- Ethereum recovers the sender's address from the signature (v, r, s); a sender cannot type a false From —
  `@wood_ethereumsecuredecentralised_2016`
- The transaction's fields, with nonce "a sequentially incrementing counter which indicates the transaction
  number from the account" — `@ethereumorg_transactions_2025`
- "Only one transaction with a given nonce can be executed for each account, protecting against replay attacks
  where signed transactions are repeatedly broadcast and re-executed" — `@ethereum.org_accountsdeveloperdocs_2025`
  (read 10 Nov 2026)
- On Bitcoin an output is spent whole and once — `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- The worked key: k from *Mastering Bitcoin* chapter 4; its Ethereum address 0xf4ddd38a2d2f4231e1ddf131a8f3fd80804e08fe;
  "a key printed in a book or tutorial is a key anyone can sign with" — `@antonopoulos_masteringbitcoinprogramming_2017` (the key itself is also in `@antonopoulos_masteringbitcoin3e_2023`, ch. 4);
  `@wood_ethereumsecuredecentralised_2016` (the Ethereum form computed for the course, 4 Nov 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Who got paid?", "Forge the payment", "Through the exchange" (10 Nov 2026)
- Built: 11 Nov 2026, `blockchain-course/assets/labs/forge-the-payment/index.html`; opened from the slide named above. Vendored @noble secp256k1 and Keccak (MIT), notice in `SOURCE.md` and `LICENSE-noble.txt`.
