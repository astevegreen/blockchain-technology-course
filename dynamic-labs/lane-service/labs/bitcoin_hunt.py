"""Terminal scavenger hunt: day 1's game in the Bitcoin lab (docs/lab-cards/terminal-scavenger-hunt.md).

The student finds five facts about block 5 with bitcoin-cli in their own terminal and pastes, for each, the
command they ran and the output line that proves it. This module serves the hunt page (labs/bitcoin_hunt/) and
checks each pasted pair:

- the command must be a bitcoin-cli call that finds that fact (the scoring key in
  quizes/microlabs/terminal_scavenger_hunt_INSTRUCTOR_ANSWERS.md);
- the line must hold the value the instructor's node holds for block 5 (the class chain is mined fresh at each
  lab start, so there is no fixed answer), or, for the confirmations, the student's own node's count, one block
  either way.

The check answers right or wrong with a reason and never sends the expected value back.
Served under /api/bitcoin/hunt/, which the router already sends to lane-service in the classroom and in the
student launcher, so no router change is needed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Optional

from flask import Blueprint, jsonify, request, send_from_directory

PAGE_DIR = Path(__file__).with_name("bitcoin_hunt")
INSTRUCTOR_CONTAINER = os.environ.get("BITCOIN_INSTRUCTOR_CONTAINER", "bitcoin-instructor-1")
DATADIR = "/home/user/.bitcoin"
BLOCK = 5
FACTS = ("count", "hash", "time", "ntx", "confirmations", "rerun")
SESSION_RE = re.compile(r"^[0-9a-f-]{36}$")

_HASH_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
_GETBLOCKHASH5_RE = re.compile(r"\bgetblockhash\s+[\"']?5[\"']?(?![\w.])")
_GETBLOCK_RE = re.compile(r"\bgetblock\b")
_FIELD_RES = {
    "time": re.compile(r"\"time\"\s*:\s*(\d+)"),
    "ntx": re.compile(r"\"nTx\"\s*:\s*(\d+)"),
    "confirmations": re.compile(r"\"confirmations\"\s*:\s*(-?\d+)"),
}
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|\b(?:am|pm|UTC|GMT)\b", re.IGNORECASE)


class NodeError(RuntimeError):
    """A node did not answer."""


def node_rpc(container: str, *args: str) -> str:
    """One bitcoin-cli call on a lab node, as the node's own user, with the datadir the orientation uses."""
    cmd = ["docker", "exec", "-u", "1000", container, "bitcoin-cli", f"-datadir={DATADIR}", *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise NodeError(f"{container}: {exc}") from exc
    if result.returncode != 0:
        raise NodeError(f"{container}: {(result.stderr or result.stdout).strip()[:200]}")
    return result.stdout.strip()


def command_problem(fact: str, command: str, block_hash: Optional[str]) -> Optional[str]:
    """Why this command does not find this fact, or None when it does."""
    cmd = " ".join((command or "").split())
    if not cmd:
        return "No command: a fact scores only with the command that found it."
    if "bitcoin-cli" not in cmd:
        return "Ask your own node: the command starts with bitcoin-cli."
    if fact == "count":
        return None if re.search(r"\bgetblockcount\b", cmd) else "That command does not ask how many blocks the node has."
    if fact == "hash":
        return None if _GETBLOCKHASH5_RE.search(cmd) else "That command does not ask for block 5's hash."
    # time, ntx, confirmations, rerun: getblock on block 5, by its hash or by getblockhash 5 inside the command.
    if not _GETBLOCK_RE.search(cmd):
        return "That command does not ask for a block's record: use getblock with block 5's hash."
    names_block5 = _GETBLOCKHASH5_RE.search(cmd) or (block_hash and block_hash.lower() in cmd.lower())
    if not names_block5:
        return "That command asks for a block, but not block 5: give getblock block 5's hash."
    return None


def line_problem(fact: str, line: str, truth: dict, previous: Optional[int] = None) -> Optional[str]:
    """Why this output line does not prove this fact, or None when it does. truth holds what the nodes hold."""
    text = (line or "").strip()
    if not text:
        return "No output line: paste the line from your terminal that shows the fact."
    if fact == "count":
        found = re.fullmatch(r"(\d+)", text.rstrip(","))
        if not found:
            return "getblockcount prints one number: paste just that line."
        n = int(found.group(1))
        return None if n in {truth.get("count_own"), truth.get("count_instructor")} else (
            "That is not how many blocks your node has now. Run the command again and paste its line.")
    if fact == "hash":
        found = _HASH_RE.search(text)
        if not found:
            return "A block hash is 64 hexadecimal characters: paste the whole line."
        return None if found.group(0).lower() == truth["hash"] else "That is not block 5's hash on the class chain."
    if fact == "time" and "mediantime" in text:
        return "That is mediantime, worked out from the last 11 blocks. Block 5's own time is the \"time\" line."
    regex = _FIELD_RES["confirmations" if fact == "rerun" else fact]
    found = regex.search(text)
    if not found:
        if fact == "time" and _DATE_RE.search(text):
            return ("That is a date, the way an explorer shows it. Your node gives the time in seconds since 1970: "
                    "paste the \"time\" line from getblock.")
        label = {"time": "\"time\"", "ntx": "\"nTx\"", "confirmations": "\"confirmations\"",
                 "rerun": "\"confirmations\""}[fact]
        return f"Paste the {label} line from getblock's output."
    n = int(found.group(1))
    if fact == "time":
        return None if n == truth["time"] else "That is not block 5's time on the class chain."
    if fact == "ntx":
        return None if n == truth["ntx"] else "That is not how many transactions block 5 holds."
    own = truth["confirmations_own"]
    if abs(n - own) > 1:
        return "That count is not your node's: run getblock on block 5 again and paste its line."
    if fact == "rerun" and previous is not None and (n <= previous or own <= previous):
        return ("The count has not grown since your fact 5. Wait for the instructor to mine a block, "
                "then run getblock again.")
    return None


def gather_truth(fact: str, student_container: Optional[str]) -> dict:
    """Read, from the instructor's node and the student's, what this fact is checked against."""
    truth: dict = {"hash": node_rpc(INSTRUCTOR_CONTAINER, "getblockhash", str(BLOCK)).lower()}
    if fact in ("time", "ntx"):
        block = json.loads(node_rpc(INSTRUCTOR_CONTAINER, "getblock", truth["hash"]))
        truth["time"] = int(block["time"])
        truth["ntx"] = int(block["nTx"])
    if fact == "count":
        truth["count_instructor"] = int(node_rpc(INSTRUCTOR_CONTAINER, "getblockcount"))
        if student_container:
            truth["count_own"] = int(node_rpc(student_container, "getblockcount"))
    if fact in ("confirmations", "rerun"):
        if not student_container:
            raise NodeError("no student node")
        block = json.loads(node_rpc(student_container, "getblock", truth["hash"]))
        truth["confirmations_own"] = int(block["confirmations"])
    return truth


def register(blueprint: Blueprint, resolve_station: Callable[[str], Optional[str]],
             container_name_fn: Callable[[str], str]) -> None:
    """Add the hunt page and its checker to the Bitcoin lab's blueprint."""

    @blueprint.route("/api/bitcoin/hunt/", methods=["GET"])
    def bitcoin_hunt_page():
        return send_from_directory(PAGE_DIR, "index.html")

    @blueprint.route("/api/bitcoin/hunt/<path:name>", methods=["GET"])
    def bitcoin_hunt_asset(name: str):
        return send_from_directory(PAGE_DIR, name)

    @blueprint.route("/api/bitcoin/hunt/check", methods=["POST"])
    def bitcoin_hunt_check():
        body = request.get_json(silent=True) or {}
        fact = str(body.get("fact", ""))
        if fact not in FACTS:
            return jsonify({"ok": False, "reason": "unknown fact"}), 400
        session = str(body.get("session") or request.cookies.get("bitcoin_session") or "").lower()
        station = resolve_station(session) if SESSION_RE.match(session) else None
        if station is None:
            return jsonify({"ok": False, "reason": "Open the hunt from your Bitcoin lab's panel bar, "
                                                   "so it can find your node."}), 401
        previous = body.get("previous")
        previous = int(previous) if isinstance(previous, int) else None
        try:
            truth = gather_truth(fact, container_name_fn(station))
        except (NodeError, ValueError, KeyError) as exc:
            return jsonify({"ok": False, "reason": "The lab's nodes did not answer just now; try again in a "
                                                   "moment.", "detail": str(exc)[:200]}), 503
        problem = command_problem(fact, str(body.get("command", "")), truth["hash"])
        if problem is None:
            problem = line_problem(fact, str(body.get("line", "")), truth, previous)
        return jsonify({"ok": problem is None, "reason": problem or "Found: your command and its line prove it."})
