# Wallet Page Flow Task

## Goal

Confirm the wallet page derives the lab's addresses and keys in the browser, as a student uses it.

## Steps

Follow "Wallet Page Flow" in `../playbook.md`, steps 1 to 9.

## Expected Results

- Dana's phrase gives receiving 0 to 3, receiving 23 after "Show 20 more", and change 0
- the passphrase `TREZOR` gives a different, valid wallet
- a bad phrase shows the error message instead of addresses
- the three phrases give the treasury's receiving and change addresses, the sorted script and a
  descriptor
- the page sends no network request while deriving

## Failure Evidence

- failing step and the values shown
- console errors
- network requests made after load
- screenshot
