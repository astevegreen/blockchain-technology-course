# The Insider: room set-up and 5-minute debrief (day 1 lab)

Instructor only. This file lives in top-level `quizes/`, which never reaches students (`CLAUDE.md`, rule 1).
The student handout is `dynamic-labs/exercises/l03-i3-trust-game/HANDOUT.md`: print it or project it.

The game opens the day 1 lab, before the 10-minute terminal orientation and the explorer worksheet. Its job is
to let students feel the problem a shared ledger solves, agreeing with people you cannot trust, before they read
their first block. The 05-IN lesson keeps its paper version of the game; this is the browser version.

## Before the lab

1. Log in once at `/instructor/`, then open `/exercises/insider/instructor`.
2. Under **Lesson Controls**, set and save:
   - **Game is online for students**: on.
   - **Backfill empty seats with bots**: on, so a room can start without waiting for a full table.
   - **Allow private rooms**: off, so every student lands in an open room and rooms fill in turn.
   - **Commit / reveal mode**: **Reveal all clues at once** is the quicker choice for a 20-minute slot. The
     one-at-a-time mode lets the Insider read earlier clues before giving one, which makes the Insider's job
     easier.
   - **Action timeout per phase**: 60 seconds.
3. Project a QR code for the lab address, ending `/exercises/insider/`. The 05-IN slide "Exercise (Digital
   Version)" carries one for the course's hosted site; on a class lab host, use that host's address.

What the app does on its own, so the timings below hold: a room takes at most six players and starts with four
or more, bots included; bots fill empty seats up to five (`app.py`: `ROOM_MAX_SIZE`, `ROOM_MIN_SIZE`,
`RECOMMENDED_GROUP_SIZE`). The handout says rooms of up to six for that reason.

## Timing (about 20 minutes, then the debrief)

| Minutes | What happens |
| --- | --- |
| 0-3 | Students join; tables share a room through the **Invite more players** QR code. |
| 3-20 | Play as many games as fit. Watch the **Active Rooms** list for a stalled room. |
| 20-25 | Turn **Game is online for students** off and run the debrief below. |

## The debrief (5 minutes)

Ask each question, take two or three answers, then land the point. Every fact below is from the one paper.

1. **"Did your room agree on who to vote out?"** That is the problem. Lamport, Shostak and Pease framed it as
   generals who can talk only by messenger, must agree on a common plan, and may include traitors trying to
   confuse the others; the requirement is that all loyal generals decide on the same plan
   [@lamport_byzantinegeneralsproblem_1982, pp. 382-383].
2. **"Why couldn't you just believe a clue?"** A clue is what the paper calls an oral message: its contents are
   completely under the sender's control, so a traitor can send anything. The paper notes that this is the kind
   of message computers normally send to one another [@lamport_byzantinegeneralsproblem_1982, p. 384].
3. **"Why does the Insider win when three players are left?"** The rule is the game's design, not the theorem,
   but it echoes it: with oral messages, no solution works unless more than two-thirds of the generals are loyal,
   so with three generals no solution can handle a single traitor, and coping with m traitors takes at least
   3m + 1 generals [@lamport_byzantinegeneralsproblem_1982, pp. 382, 384-385].
4. **"What would have made agreeing easier?"** Something you can check instead of someone you must believe. The
   paper assumes that a loyal general's signature cannot be forged, that any change to a signed message can be
   detected, and that anyone can check a signature; with such unforgeable written messages, the problem is
   solvable for any number of generals and traitors [@lamport_byzantinegeneralsproblem_1982, pp. 382, 391].
   Hand-off: today's lessons covered keys, signatures and how a public ledger agrees; the explorer worksheet
   that follows reads the record that agreement produces.

## Answers to look for (the handout's five questions)

1. A clue specific enough to prove you know the word also helps the Insider guess it: the honest players leak
   what they are protecting.
2. Suspicion rests on behaviour as much as content: a vague clue, a late lock-in, a vote that follows the crowd.
3. No one can check who is right, only who seems right, so a room can split or change its mind as votes come in.
4. Each wrong vote removes an honest player while the Insider stays in; if the Insider is still in when three
   players are left, the Insider wins.
5. A record or proof that others cannot fake: the bridge to point 4 of the debrief.
