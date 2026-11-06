# Micro-lab answers: reading a contract with no source

Instructor only. The student page is `blockchain-course/assets/labs/ether_evm/index.html`, linked from 11-FO's
"How sure: what a code read rests on" slide (and as a day-8 preview from 01-EF). It is practice, not graded. Every
answer traces to 11-FO's Part 1 slides; the contract, addresses and transactions are made up, the selectors are real.

## The problem contract (`0xc0de…7e57`, no verified source)

Storage: slot 1 = `0xa11ce…` (the only caller allowed to run `42966c68`), slot 2 = `0xfee…` (the fee address),
slot 3 = 2 (the fee, in percent).

1. **Selectors and looked-up names.**
   - `0xa9059cbb`: `transfer(address,uint256)` (11-FO, selector slide).
   - `0x42966c68`: two signatures on file, `burn(uint256)` and `collate_propagate_storage(bytes16)`.
2. **What each function lets its caller do, and who may call it.**
   - `a9059cbb`: anyone may call it. It moves the caller's own tokens to `arg0`, minus a fee of `storage[3]`
     percent (2%), which goes to the address in slot 2 (`0xfee…`). A standard `transfer` takes no fee.
   - `42966c68`: only the address in slot 1 (`0xa11ce…`) may call it. It adds `arg0` new tokens to that address's
     balance and to `storage[0]` (likely the total supply; the name is a guess), and logs a `Transfer` from the zero
     address: it creates tokens for the owner.
3. **What P1 and P2 did.**
   - P1: `0xa11ce…` called `42966c68` with 1,000,000; the log shows 1,000,000 new tokens created to `0xa11ce…`.
   - P2: `0xb0b…` called `a9059cbb` to send 250 to `0xcafe…`; the logs show 245 to `0xcafe…` and 5 to `0xfee…`.
4. **Do the names match?** `transfer`: partly; it transfers, but takes a 2% fee a standard transfer does not.
   `burn`: no; the code creates tokens for the owner, the opposite of burning (11-FO, "a name, not proof").
5. **Sentences for an agent** (11-FO, "How sure"):
   - "Function `0xa9059cbb` moves the caller's tokens and sends 2% to `0xfee…`; P2 shows 5 of 250 going there."
     Moderate: decompiled code and the logs agree, but the decompiler can misread. Verified source that matches
     would make it High.
   - "Function `0x42966c68` lets only `0xa11ce…` create new tokens for itself; P1 created 1,000,000."
     Moderate, for the same reason. The looked-up name `burn` adds no confidence and should not be repeated
     as what the function does.
   - A student who answers from the decompiled code alone, without the logs, should write Moderate at best.

## Optional challenge

6. Report `burn(uint256)` as the signature the selector matches, while saying the code mints. Read as
   `bytes16`, the argument leaves non-zero bytes after the first 16, which a correct encoding never does (ABI
   specification: `bytes<M>` is padded with trailing zeros); read as `uint256` it is a sensible 1,000,000. Either way
   the name says nothing about what the code does.
7. "The contract takes 2% of every transfer and sends it to `0xfee…`. Bob's 250 became 245 for `0xcafe…` and 5 for
   the fee address." Slot 3 sets the share; slot 2 sets the receiver.
8. Two different signatures give the same four bytes: a lookup can return more than one name, and any of them is
   only what someone submitted (11-FO, lookup slide). Confirm from the code and the logs.

## Worked example (on the page with its answers)

The sorting table checks itself: selector, condition and storage writes are "usually recovered"; the names and the
comment are "not recovered"; the types "can be wrong" (11-FO, decompiler table).
