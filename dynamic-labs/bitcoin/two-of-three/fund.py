#!/usr/bin/env python3
"""Set up the day 2 game "Two of three" on a running Bitcoin lab (design card: docs/lab-cards/two-of-three.md).

Instructor only: this file names the indexes round 2 asks students to find, so it is on
dynamic-labs/student-exclude.txt. Run it on the lab host, where `docker` reaches the lab's containers:

    python3 dynamic-labs/bitcoin/two-of-three/fund.py                 # every running student, paired 1:2, 3:4, ...
    python3 dynamic-labs/bitcoin/two-of-three/fund.py --pairs 1:2,3:4  # pairs chosen by hand
    python3 dynamic-labs/bitcoin/two-of-three/fund.py --pairs 5:instructor

An odd student out is paired with the instructor's own node ("instructor"), which then plays the partner.

For each pair it:
  - makes a key wallet `two-of-three-key` in each partner's node, and an "away" key on the instructor's node;
  - makes a wallet `two-of-three` in each partner's node that watches wsh(sortedmulti(2, own key, partner's key,
    away key)) and can sign with its own key only (the wallet lab's treasury descriptor);
  - pays the pair's first address from the instructor's seed wallet.
For each student it makes a wallet `game-account` and pays three of its receiving indexes (one beyond index 4),
then writes ~/two-of-three/partner-host and ~/two-of-three/classmate.xpub into the student's home.

It prints the answer sheet and writes it to answers-<UTC time>.md beside this script (git-ignored).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

INSTRUCTOR = "bitcoin-instructor-1"
STUDENT_PREFIX = "bitcoin-lab-student"
SEED_WALLET = "instructor_seed"
KEY_WALLET = "two-of-three-key"
PAIR_WALLET = "two-of-three"
GAME_WALLET = "game-account"
PAIR_AMOUNT = 0.5
INDEX_AMOUNT = 0.1
# The easiest block ClassNet allows after 20 s (mine-until's own rule): above the ceiling a block costs CPU.
EASIEST_BITS = "207fffff"
DIFFICULTY_CEILING = 0.00025


class FundError(RuntimeError):
    pass


def paid_indexes(station: int) -> list[int]:
    """The three receiving indexes paid into a station's game account; the third is always beyond index 4."""
    return [station % 2, 2 + station % 2, 5 + station % 4]


def run(container: str, command: str, *, timeout: int = 120, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["docker", "exec", *(["-i"] if stdin is not None else []), container, "bash", "-lc", command],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise FundError(f"{container}: `{command}` failed: {(result.stderr or result.stdout).strip()[:400]}")
    return result.stdout.strip()


def cli(container: str, *args: str, wallet: str | None = None, timeout: int = 120) -> str:
    parts = ["bitcoin-cli"] + ([f"-rpcwallet={wallet}"] if wallet else []) + list(args)
    return run(container, " ".join(shlex.quote(p) for p in parts), timeout=timeout)


def cli_json(container: str, *args: str, wallet: str | None = None, timeout: int = 120):
    return json.loads(cli(container, *args, wallet=wallet, timeout=timeout))


def ensure_wallet(container: str, name: str, *, blank: bool = False) -> None:
    if name in cli_json(container, "listwallets"):
        return
    try:
        cli(container, "loadwallet", name)
    except FundError:
        cli(container, "-named", "createwallet", f"wallet_name={name}", f"blank={'true' if blank else 'false'}")


def account_keys(container: str, wallet: str) -> tuple[str, str]:
    """The wallet's BIP 84 account key as (private key with its path, public key with its origin)."""
    private = cli_json(container, "listdescriptors", "true", wallet=wallet)["descriptors"]
    public = cli_json(container, "listdescriptors", wallet=wallet)["descriptors"]

    def external_wpkh(descriptors: list[dict]) -> str:
        for entry in descriptors:
            if entry["desc"].startswith("wpkh(") and not entry.get("internal"):
                return entry["desc"]
        raise FundError(f"{container}: wallet {wallet} has no wpkh receiving descriptor")

    match_priv = re.fullmatch(r"wpkh\((.+)/0/\*\)#\w+", external_wpkh(private))
    match_pub = re.fullmatch(r"wpkh\((.+)/0/\*\)#\w+", external_wpkh(public))
    if not match_priv or not match_pub:
        raise FundError(f"{container}: cannot read the account key of wallet {wallet}")
    return match_priv.group(1), match_pub.group(1)


def with_checksum(container: str, descriptor: str) -> str:
    checksum = cli_json(container, "getdescriptorinfo", descriptor)["checksum"]
    return f"{descriptor}#{checksum}"


def multisig(keys: list[str], branch: int) -> str:
    return "wsh(sortedmulti(2," + ",".join(f"{key}/{branch}/*" for key in keys) + "))"


def wait_for_height(container: str, height: int, timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if int(cli(container, "getblockcount")) >= height:
            return
        time.sleep(1)
    raise FundError(f"{container} did not reach block {height} within {timeout} s")


def mine_one(address: str) -> int:
    """Mine one block on the instructor's node, waiting for an easy one as mine-until does."""
    deadline = time.time() + 120
    start = int(cli(INSTRUCTOR, "getblockcount"))
    while time.time() < deadline:
        nxt = cli_json(INSTRUCTOR, "getmininginfo").get("next", {})
        hard = nxt.get("difficulty", 0) > DIFFICULTY_CEILING and nxt.get("height", 0) % 2 == 1
        if hard and nxt.get("bits") != EASIEST_BITS:
            time.sleep(1)
            continue
        if cli_json(INSTRUCTOR, "generatetoaddress", "1", address, "50000000", timeout=180):
            return start + 1
        time.sleep(1)
    raise FundError("the instructor's node could not mine a block in 120 s")


def running_stations() -> list[int]:
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=True
    ).stdout.split()
    return sorted(int(name[len(STUDENT_PREFIX):]) for name in out if re.fullmatch(STUDENT_PREFIX + r"\d+", name))


def parse_pairs(text: str | None, stations: list[int]) -> list[tuple[int, int | None]]:
    """Pairs of station numbers; None stands for the instructor's node."""
    if text:
        pairs = []
        for item in text.split(","):
            left, right = item.split(":")
            pairs.append((int(left), None if right == "instructor" else int(right)))
        return pairs
    pairs = [(stations[i], stations[i + 1]) for i in range(0, len(stations) - 1, 2)]
    if len(stations) % 2:
        pairs.append((stations[-1], None))
    return pairs


def classmate_for(station: int, students: list[int], pairs: list[tuple[int, int | None]]) -> int:
    """Whose game account a student watches in round 2: the station two along, or the partner when only two play.

    A lone student paired with the instructor watches their own account."""
    if len(students) > 2:
        return students[(students.index(station) + 2) % len(students)]
    for left, right in pairs:
        if station in (left, right):
            other = right if station == left else left
            return station if other is None else other
    return station


def container_of(station: int | None) -> str:
    return INSTRUCTOR if station is None else f"{STUDENT_PREFIX}{station}"


def label(station: int | None) -> str:
    return "instructor" if station is None else f"station {station}"


def write_home_file(container: str, name: str, text: str) -> None:
    run(container, f'mkdir -p "$HOME/two-of-three" && cat > "$HOME/two-of-three/{name}"', stdin=text + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--pairs", help="pairs such as 1:2,3:4 or 5:instructor (default: every running student)")
    parser.add_argument("--answers", type=Path, help="where to write the answer sheet")
    args = parser.parse_args(argv)

    stations = running_stations()
    pairs = parse_pairs(args.pairs, stations)
    students = sorted({s for pair in pairs for s in pair if s is not None})
    if not students:
        raise FundError("no running student stations (bitcoin-lab-studentN) to set up")

    # The instructor's seed wallet must hold enough mature coins to pay every pair and every game account.
    ensure_wallet(INSTRUCTOR, SEED_WALLET)
    need = PAIR_AMOUNT * len(pairs) + 3 * INDEX_AMOUNT * len(students) + 0.01
    seed_address = cli(INSTRUCTOR, "getnewaddress", wallet=SEED_WALLET)
    run(INSTRUCTOR, f"mine-until {SEED_WALLET} {seed_address} {need:.8f}", timeout=900)

    ensure_wallet(INSTRUCTOR, "two-of-three-away")
    _, away_pub = account_keys(INSTRUCTOR, "two-of-three-away")

    sheet = [f"# Two of three: answer sheet ({dt.datetime.now(dt.timezone.utc):%d %b %Y %H:%M} UTC)", ""]
    sheet += ["## Round 1: each pair's coin", "", "| Pair | 2-of-3 address | Funding txid |", "| --- | --- | --- |"]
    for left, right in pairs:
        keys = {}
        for station in (left, right):
            wallet = KEY_WALLET if station is not None else f"{KEY_WALLET}-for-{left}"
            ensure_wallet(container_of(station), wallet)
            keys[station] = account_keys(container_of(station), wallet)
        address = None
        for station, partner in ((left, right), (right, left)):
            container = container_of(station)
            wallet = PAIR_WALLET if station is not None else f"{PAIR_WALLET}-with-{left}"
            ensure_wallet(container, wallet, blank=True)
            own_priv = keys[station][0]
            signers = [own_priv, keys[partner][1], away_pub]
            imports = [
                {"desc": with_checksum(container, multisig(signers, branch)), "active": True,
                 "internal": bool(branch), "timestamp": "now", "range": [0, 20]}
                for branch in (0, 1)
            ]
            result = cli_json(container, "importdescriptors", json.dumps(imports), wallet=wallet)
            if not all(item.get("success") for item in result):
                raise FundError(f"{container}: importdescriptors failed: {result}")
            first = cli_json(container, "deriveaddresses", with_checksum(
                container, multisig([keys[station][1], keys[partner][1], away_pub], 0)), "[0,0]")[0]
            if address not in (None, first):
                raise FundError(f"the two partners of {label(left)} derive different addresses")
            address = first
            if station is not None:
                write_home_file(container, "partner-host", container_of(partner))
        txid = cli(INSTRUCTOR, "sendtoaddress", address, f"{PAIR_AMOUNT}", wallet=SEED_WALLET)
        sheet.append(f"| {label(left)} + {label(right)} | `{address}` | `{txid}` |")

    # Round 2: each student's game account, paid at three indexes; each student watches a classmate's account.
    accounts = {}
    payments = {}
    for station in students:
        container = container_of(station)
        ensure_wallet(container, GAME_WALLET)
        _, xpub = account_keys(container, GAME_WALLET)
        accounts[station] = xpub
        descriptor = with_checksum(container, f"wpkh({xpub}/0/*)")
        payments[station] = []
        for index in paid_indexes(station):
            to = cli_json(container, "deriveaddresses", descriptor, f"[{index},{index}]")[0]
            txid = cli(INSTRUCTOR, "sendtoaddress", to, f"{INDEX_AMOUNT}", wallet=SEED_WALLET)
            payments[station].append((index, to, txid))

    block = mine_one(seed_address)
    for station in students:
        wait_for_height(container_of(station), block)

    classmate_of = {station: classmate_for(station, students, pairs) for station in students}
    for station, classmate in classmate_of.items():
        write_home_file(container_of(station), "classmate.xpub", accounts[classmate])

    sheet += ["", f"All funding confirmed in block {block}.", "", "## Round 2: whose account each student watches", ""]
    sheet += ["| Student | Watches | Paid index | Address | Block |", "| --- | --- | --- | --- | --- |"]
    for station, classmate in classmate_of.items():
        for index, to, _txid in payments[classmate]:
            sheet.append(f"| {label(station)} | {label(classmate)} | {index} | `{to}` | {block} |")

    text = "\n".join(sheet) + "\n"
    print(text)
    out = args.answers or Path(__file__).with_name(f"answers-{dt.datetime.now(dt.timezone.utc):%Y%m%d-%H%M%S}.md")
    out.write_text(text, encoding="utf-8")
    print(f"answer sheet written to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FundError as error:
        print(f"fund.py: {error}", file=sys.stderr)
        sys.exit(1)
