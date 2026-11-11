# Bitcoin Forensics — Instructor Reference

The student-facing curriculum is the live lab guide (**Bitcoin Forensics 1**, **Bitcoin
Forensics 2**, and **Bitcoin Forensics 3**), served from the exercise catalog. This file is the
**instructor answer key** for the deployed 3-part chain (jittered v34 + v35 + v36), shown in the
admin panel via "show forensics solution key" and also revealable to students per-step with the
F1 / F2 / F3 "Show Solutions" toggles.

All txids/addresses below are verbatim from the live chain.

## Instructor Solution Key

### Bitcoin Forensics 1 (jittered v34) — chain region: earlier blocks

Marquee skill: **behavioral de-anonymization** — of five identical CoinJoin outputs, four go quiet and one keeps moving.

- **Lead / ransom deposit:** `bc1qpxa098jvglpcy82u43lpyc66h8674ztxqtcf2k`
- **Ransom:** `ff808f8495336f9f8c1cff121ae607813dc0e9e3e5111ef23aaa6b974d355bce` — **768.76397251 BTC**, multi-input (CIOH: the victim's coinbase coins co-spent into one payment).
- **CoinJoin:** `5738c1b5ddce04a65b76fa2871d0acc87edda70835d7607b7d6c6ce774402c22` — five equal outputs of 768.76397251 BTC. Four are whale decoys that spend once to cold storage and go dormant; the attacker's output **continues** at `bc1qemlv5k5mrky8fqn5gskmqtr923qndyps4ptjgl`.
- **Fan-out:** `6c2feac4e9a3da08fb2e98892ae9433bc4dfb1aa310c86c8f028e64991a79cfb` — five **unequal/jittered** chunks (~78.27, 145.37, 97.84, 232.03, 215.25 BTC).
- **Peel chains:** each chunk runs a 3-hop peel (small peel + continuing remainder per hop). Chunk 0 (start `bc1qewhamkx46gxepc08xhf04lnh0vc279wx7scf83`): hop txids `fbff1b588c6f24119c793c091fcc9205027fbf9dd575c2dc8204ea60eb5dab67` → `1e01734d7539e7b2e6667f04050ec7bff6f2783457a6652652ab66409834ab44` → `06be16ffa22e032e684f8d7c1416f2edc909e82a4f0f2ef313dc55c0ed370e76`. The five chain tips reunite at the consolidation.
- **Consolidation:** `9ca9c8d7f52fdade568c5c0892cfd9959e66f1a56e7e35693d98c39137c1e436` — all five tips → vault `bc1qe8hxxjwhwcy57mt2p5q7srkmw6j2x7yf5n6v6d`, holding **768.73797251 BTC** (ransom − ~0.026 BTC total fees).
- **Taunt:** `1b7e209d16596609c68fcf482a31d09135a359858ba3e8b4566ca7b010468e02` — OP_RETURN ASCII **`HACKY HACK HACK`** + four 546-sat dust outputs; final address `bc1qes52mtttw3ue29qgehrgm53mnpunh9d4kxtw8z`.

### Bitcoin Forensics 2 (v35) — chain region: later blocks

Headline skill: **temporal analysis** — three lookalike decoys batch into one block; the real exit is held back ~12 blocks.

- **Lead / ransom deposit:** `bc1qgavytp7u2kqyffefv3p0rvu2gtj02ka2hlleet`
- **Ransom:** `e95d48d859ca53e6e2d666276e2c486923e9c0c4173924abbcb90cdead07fd0a` — **728.12292303 BTC**, non-round, CIOH. First layering hop `42a3ab0eba94f243b81450ff863f3b70e4aa8af0fb53cdc58eb69bdceb1c8972`.
- **Fan-out (six):** `55cec00737582f5bb74971e0bbf033f764133d0e6d3060acf54f361ae1f24379` — chunks pre-sized to ~121.35 BTC for the joins.
- **Three CIOH-leaky 3-way CoinJoins** (each: 2 attacker chunks + 1 unrelated decoy, three equal ~121.35 BTC outputs): `a8fa0783b54db97cecaa36231ad64e1e1f6e969b7860e7a0015aaaf5f1e798fd`, `77ee00e29a0e53e13ec7a019f76bb5042448566163582ed88dc674f0d55ad3db`, `7f45aef83af17a968bc7ba0cb06a7c55c793c7932fa029baacc835de9fad3733`. The two co-spent attacker inputs leak common ownership despite the equal outputs.
- **The tangle (obfuscation — trace value is conserved, only fees leak):**
  - Smurf `ddab32a595c3e7f859dcfad09d0e576b2d3628e984042ec95c8de759d6c0081e` → 24+ tiny pieces.
  - Churn round-trips (A→B→A, net zero): `15135de008852ab3a1d2918f4d0745758def82d0d42b3932a01bea3913b8724e` ↔ `76666562dd528a465186139fa83288d555f6c7dc8b3f73380e4ade8a9dfe1cb2`; `7935033dd4a336711d71f29215de0f2cada0390fd4e6fb77e17f7a8250e64e39` ↔ `aa2cefb8661a3d306ce6a9269b55a1cb81488797cb13c472b48cc21c00f6554b`.
  - Unrelated-coin touches (false-cluster bait — ignore the off-trail inputs): `ead0e60f5a7374df8c6c12ca463ec2454ed8088da94099a3fcbe5686a54bcc3e`, `f9dd0a3010ee80d28a8d8ab7f4615c442c3fa22ff318496e4af0582f2feeb34c`.
- **Recombine:** `acde5901314b60ecc090944568c42457aa7814f9b1b67b806be658643c37024a` (CIOH — gathers the smurf pieces). **Peel:** `b8f3879829fc37500f348eab3734650a76abf860037eebcb0026de05ebca8880` → `65373373164fd1bc73ff8ac736a6124b41a2468a4455e5274ae9816953225338`.
- **Three lookalike decoy flows** (~121.35148717 BTC each), endpoints `bc1qug47crvzmlva2k6qycymjglxjt2thfaxxvnuj9`, `bc1qrv5n3474xkry99fag26gdul7n7ct8sx6kcxkdl`, `bc1q075p27hs086nwwjw3zaaqy09vwp8ggdt50palu`; final-move txids `42f5f55f733caaecb442fd2b460e5c14dd794e239f5dfa33f46c40c5d3aa5c37`, `c7315bc2aa501d0fa8e0c6d62dd69b742adb5347dc91dcd2ed48be18247bb897`, `0f9bb38c3f2f317a03ab0b7e0ecd42893a96b2af0618d148dcb721e5486fa729`.
- **The temporal tell:** all three decoy moves confirm in **block 245**; the real cash-out confirms in **block 257** — a **12-block gap**. Structure/value tie the four candidates; only timing separates them.
- **Cash-out:** `7e5b2ef93556e25855f3aa92aa3481a30ad597b1d4d0ab0082aca1d3611a2a06` (block 257) → vault `bc1qq4llyczrmrcddxrpnsv7a0rguuj3k4endpc096` (**730.45740649 BTC**). It co-mingles exactly two inputs: the trace tip + one small off-trail input (~3.17 BTC, prep `63be945643b581678a2f0557abeebd6be0a0953a9a1ac2da437280dab5016a32`) — back it out for the trace-only recovered figure (ransom − fees). Final address `bc1q6x0fm2kje5vp3pp3x5dzqukgh574982mhl8v8p`.
- **Taunt:** `a4ac7576fcd703f259fc738a373a4938f6c947cd8df13c72e7ed281c238ab0b5` — single OP_RETURN ASCII **`HACKY HACK HACK`** (no decoy taunts).

### Bitcoin Forensics 3 (v36) — chain region: latest blocks

Headline skill: **amount-conservation against a *real* CoinJoin, plus decoy disambiguation.** Two ransoms are merged into one stake `Q`; the coin then passes through two genuine multi-party mixes where common-input clustering **lies** (it over-clusters honest strangers). Only the conserved value `Q` threads both joins, and among one true trail and five lookalike decoy cash-outs only the trail that conserves `Q` is real — confirmed by a temporal hold and the signature taunt.

- **Two leads / two ransoms (CIOH → merge):** Victim A pays lead A `bc1qs3achyr4wxmxklw6wus29ky3wtdkflyztwethc` (**67.79542917 BTC**); victim B pays lead B `bc1qlh5cxjmas0ys3hsw9c8qeaz6paf9gv9dcxnljy` (**57.17505052 BTC**). Ransom A `210d46b1b8bff0540d869683f9110227b7bbb23759d4f683a64b8894ccaa572b`, ransom B `87e3dbd6d0e27f06582720aabc83f78398523f0b67d517f59d895e91a6ba129c` — both CIOH. The brief gives only lead A; lead B is discovered from the merge's second input.
- **Merge:** `7a07919b3cfe58469d65de5c757dd27aca059071141a8d99614f237443dc541e` co-spends both leads into one stake `bc1q09u2llhc9p9gdwszskl69hu9un4pa9hh2wnu3u` of **Q = 124.96947969 BTC** (= 67.79542917 + 57.17505052 − 0.001 fee). `Q` is the conserved quantity.
- **First real CoinJoin (8-party):** `05da0aaa06f45705285c7049a9f7f9bf5266ef54d1b756503669f6b56cb5988d` — 8 inputs from 8 distinct owners, **8 equal outputs of 124.96847969 BTC**. A *real* mix: CIOH falsely over-clusters all eight. By amount-conservation the attacker's output is `bc1q7gev63ghngw82l04ytsmuq6u58sa8xzq4f6hqe`. The 7 honest peers each spend once to cold storage and dead-end (e.g. peer-1 `0059844567366c8a8be564187f0a02981eb9c0d2b6ad0959435e1c70c5d1ef4d`, peer-7 `65f1060130d1aab16c52c39ffbd661bf622c0b2a802e6bc9b61c61603eaa4de9`).
- **Nested real CoinJoin (7-party):** `423013791b34d0f0fc2d0e26b78e36a9ca833ea411c7d4b67f89a86d51516608` — the attacker's first-mix output + 6 fresh peers, **7 equal outputs of 124.96747969 BTC**. Attacker's output continues at `bc1qfmrzysxc95hwvtcsztgu9jx3h0vm88zpvxu8wd`; the 6 peers dead-end (e.g. peer-1 `94969f9cf236b24d06ad1c6feeab18ee43cf4c768c2d28cb33b032e47b5485f4`, peer-6 `3c6ee4c0af894e6a9fd9754bd1e02070769c9ee7abe3fefc3468e303568e9146`). Across both joins **13 honest peers dead-end**; clustering is useless, only conservation threads the mixes.
- **Branch (true trail + separate decoy pool):** twice-mixed, the coin layers once via `bdcbfb1f8e9d19cd753303dd09ebb98b5402fa574f0b73661952aac49686b3ae` → `bc1qhlyj6uhmq37v8nnxh5cdy80ddz3jm70p39g846` (**124.96647969 BTC**, ≈ Q) — the true trail. Independently a `decoy_funder` seeds **five decoy cash-out trails** from a separate, smaller pool; endpoints `bc1qfk9wsa6kjdm2v9kmljh4963j34k6ka895w3mp2`, `bc1q70ckxysr4m2vxyec5z9q8mr8cpt77e3za6syue`, `bc1q4sn9cqmxy42nc700er0wt0237nhl2z8z3l7s06`, `bc1q2lkzxdl7h3d4tn6n6hcxmc98vv9cunv9txelzv`, `bc1qrv4wj4a5swn5legf4my7n8vzqwv53twcultesq` (final moves `25f64ce218965fffd8cc800027fa3829cb91c6569228ad8170f10e3c505fc177`, `46d10211cd6287c6833696e23b9c18a14ad3a5188f7ae10f08a503bd5b86e0cc`, `b9e9bbd98b69562c0bcd11f0eb9261ced42b88cd4814bb40fbe0adfb0b7945d5`, `a018a7ff1e9dd653fbebdc7059faf443f5e3e8be3d08693ab448ae658bcc4d66`, `209cb8e0ac83f70aee8b34b423ff327947c65c2c0b92511ce0662d2ae42ecb22`).
- **Amount-conservation + the peel re-gather:** each decoy endpoint holds only **8.00000000 BTC** — an order of magnitude below Q, so value alone excludes all five. The true cash-out **re-gathers a 3-hop peel chain**: 4 inputs = train tip 122.75106393 + peels 0.59654541 / 0.73626388 / 0.87960647 = **124.96347969 BTC**; following the largest output alone would undercount by the three peels.
- **Temporal tell:** all five decoy moves confirm in **block 323**; the real cash-out is held to **block 332** — a **9-block hold**. Value and time agree on the same transaction.
- **Cash-out:** `dbdb1eecadfe1ab420839163028cbe54f0546277b0256685c11354cbcad9e536` (block 332) → vault `bc1qp24fx94ndlzq8yy73jajxk30hxfth7nzmtsypt` (**124.95347969 BTC** = Q − cumulative fees). It carries the OP_RETURN ASCII **`HACKY HACK HACK`** signature; **no decoy does**. Every one of the five decoy endpoints is marked **`DEAD END`**.
- **Recovered:** **Q = 124.96947969 BTC** across the two ransoms; ≈ 124.95347969 BTC survives to the vault after fees.
