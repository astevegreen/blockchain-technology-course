import os
import random
import secrets
import string
import time
from importlib.metadata import PackageNotFoundError, version as package_version
from io import BytesIO
from functools import wraps

import qrcode
from flask import Flask, render_template, request, send_file, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.middleware.proxy_fix import ProxyFix

from instructor_auth import (
    AuthConfig,
    AuthMode,
    csrf_blueprint,
    install_csrf_protection,
    install_login_rate_limit,
    install_sliding_reissue,
    require_instructor,
    standalone_blueprint,
    verify,
)
from word_bank import AGENT_CLUE_BANK, SECRET_WORDS


def validate_socketio_stack():
    try:
        python_socketio_version = package_version("python-socketio")
        python_engineio_version = package_version("python-engineio")
    except PackageNotFoundError as exc:
        raise RuntimeError("The Socket.IO server dependencies are not installed correctly.") from exc

    if not python_socketio_version.startswith("5.") or not python_engineio_version.startswith("4."):
        raise RuntimeError(
            "Incompatible Socket.IO stack detected. "
            f"python-socketio={python_socketio_version}, "
            f"python-engineio={python_engineio_version}. "
            "This app requires python-socketio 5.x and python-engineio 4.x."
        )


validate_socketio_stack()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "blockchain-course-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

ROOM_MAX_SIZE = 6
ROOM_MIN_SIZE = 4
RECOMMENDED_GROUP_SIZE = 5
DEFAULT_DISCONNECT_GRACE_SECONDS = 15
ACTION_TIMEOUT_SECONDS = 60
DEFAULT_RETENTION_MINUTES = 60
MIN_RETENTION_MINUTES = 1
MAX_RETENTION_MINUTES = 1440
INSTRUCTOR_DASHBOARD_ROOM = "instructors"

# Phase 7.7: auth verification + issuance lives in the shared
# instructor_auth package (copy-vendored into the build context).
# AuthConfig.from_env() raises at import time if the secret is missing
# in production, so a misconfigured deploy fails fast.
_auth_config = AuthConfig.from_env()
app.config["INSTRUCTOR_AUTH"] = _auth_config


AGENT_NAMES = [
    "Alex",
    "Blair",
    "Casey",
    "Devon",
    "Emery",
    "Finley",
    "Harper",
    "Jordan",
    "Logan",
    "Morgan",
    "Parker",
    "Reese",
    "Riley",
    "Sawyer",
    "Taylor",
]

GENERIC_CLUES = [
    "object",
    "place",
    "motion",
    "color",
    "sound",
    "shape",
    "daily",
]

GAME_SETTINGS = {
    "game_enabled": True,
    "disconnect_grace_seconds": DEFAULT_DISCONNECT_GRACE_SECONDS,
    "action_timeout_seconds": ACTION_TIMEOUT_SECONDS,
    "retention_minutes": DEFAULT_RETENTION_MINUTES,
    "agents_enabled": True,
    "private_rooms_enabled": True,
    "reveal_mode": "random",
    "context": "A group shares a secret word. One Insider does not know it and must blend in.",
    "custom_words": "",
}

# Single-process in-memory state for classroom deployments.
rooms = {}
player_to_room = {}
sid_to_player = {}


def requires_auth(f):
    """Decorator: require a valid instructor cookie and mirror the
    truthy `session['is_instructor']` flag so Socket.IO event handlers
    (which check the flask session) see the authenticated state."""
    @require_instructor(_auth_config)
    @wraps(f)
    def decorated(*args, **kwargs):
        # require_instructor has already verified the cookie — if we
        # reach here the request is authenticated.
        session["is_instructor"] = True
        return f(*args, **kwargs)
    return decorated


if _auth_config.mode is AuthMode.STANDALONE:
    app.register_blueprint(standalone_blueprint(_auth_config))

app.register_blueprint(csrf_blueprint(_auth_config))
install_sliding_reissue(app)
install_csrf_protection(app, _auth_config)

if _auth_config.mode is AuthMode.STANDALONE:
    try:
        install_login_rate_limit(
            app,
            login_endpoints=["instructor_auth_standalone.login"],
        )
    except Exception as _rl_err:
        import sys as _sys
        _sys.stderr.write(f"[trust-game] WARNING: rate limiter not installed: {_rl_err}\n")


def active_secret_words():
    custom_words = [
        line.strip()
        for line in GAME_SETTINGS["custom_words"].splitlines()
        if line.strip()
    ]
    return custom_words or SECRET_WORDS


def game_is_online():
    return GAME_SETTINGS["game_enabled"]


def disconnect_grace_seconds():
    return max(0, int(GAME_SETTINGS["disconnect_grace_seconds"]))


def action_timeout_seconds():
    return max(15, int(GAME_SETTINGS["action_timeout_seconds"]))


def retention_minutes():
    return max(
        MIN_RETENTION_MINUTES,
        min(MAX_RETENTION_MINUTES, int(GAME_SETTINGS["retention_minutes"])),
    )


def normalized_name(text):
    return " ".join(text.strip().lower().split())


def create_player(name, is_agent=False):
    return {
        "name": name,
        "connected": not is_agent,
        "active": True,
        "is_agent": is_agent,
        "sid": None,
        "role": None,
        "disconnect_deadline": None,
        "status_reason": None,
        "agent_memory": {},
    }


def generate_player_id():
    return secrets.token_urlsafe(9)


def generate_room_id():
    while True:
        room_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if room_id not in rooms:
            return room_id


def create_room(private_room=False):
    room_id = generate_room_id()
    rooms[room_id] = {
        "players": {},
        "private_room": private_room,
        "roster_locked": False,
        "state": "lobby",
        "round": 0,
        "insider_sid": None,
        "word": None,
        "votes": {},
        "result": None,
        "game_over": False,
        "clues": {},
        "revealed_clues": [],
        "reveal_queue": [],
        "turn_order": [],
        "current_turn_index": 0,
        "phase_deadline": None,
        "phase_kind": None,
        "phase_turn_sid": None,
    }
    return room_id


def get_or_create_room():
    for room_id, room in rooms.items():
        if (
            room["state"] == "lobby"
            and not room.get("archived")
            and not room["private_room"]
            and not room["roster_locked"]
            and active_player_count(room) < ROOM_MAX_SIZE
        ):
            return room_id
    return create_room()


def get_requested_room(room_id):
    if not room_id:
        return None
    room_id = room_id.strip().upper()
    room = rooms.get(room_id)
    if (
        not room
        or room.get("archived")
        or room["state"] != "lobby"
        or active_player_count(room) >= ROOM_MAX_SIZE
    ):
        return None
    return room_id


def current_room():
    room_id = player_to_room.get(request.sid)
    return room_id, rooms.get(room_id)


def current_player_id():
    return sid_to_player.get(request.sid)


def player_payload(room, sid):
    player = room["players"][sid]
    return {
        "id": sid,
        "name": player["name"],
        "connected": player["connected"],
        "active": player["active"],
        "has_voted": sid in room["votes"],
        "has_committed_clue": sid in room["clues"],
        "is_agent": player["is_agent"],
        "role": player["role"],
        "status_reason": player["status_reason"],
    }


def attach_socket_to_player(room_id, player_id, sid):
    room = rooms[room_id]
    player = room["players"][player_id]
    player["sid"] = sid
    player["connected"] = True
    player["active"] = True
    player["disconnect_deadline"] = None
    if player["status_reason"] == "disconnected":
        player["status_reason"] = None
    player_to_room[sid] = room_id
    sid_to_player[sid] = player_id


def detach_socket(sid):
    player_id = sid_to_player.pop(sid, None)
    room_id = player_to_room.pop(sid, None)
    return room_id, player_id


def active_player_ids(room):
    return [sid for sid, player in room["players"].items() if player["active"]]


def active_human_ids(room):
    return [
        sid
        for sid, player in room["players"].items()
        if player["active"] and not player["is_agent"]
    ]


def active_player_count(room):
    return len(active_player_ids(room))


def room_payload(room_id):
    room = rooms[room_id]
    current_turn_sid = active_turn_sid(room)
    return {
        "room_id": room_id,
        "state": room["state"],
        "round": room["round"],
        "max_size": ROOM_MAX_SIZE,
        "min_size": ROOM_MIN_SIZE,
        "players": [player_payload(room, sid) for sid in room["players"]],
        "player_count": active_player_count(room),
        "game_over": room["game_over"],
        "votes_cast": len([sid for sid in room["votes"] if room["players"].get(sid, {}).get("active")]),
        "clues_committed": len([sid for sid in room["clues"] if room["players"].get(sid, {}).get("active")]),
        "revealed_clues": room["revealed_clues"],
        "result": room["result"],
        "private_room": room["private_room"],
        "current_turn_sid": current_turn_sid,
        "current_turn_name": room["players"][current_turn_sid]["name"] if current_turn_sid else None,
        "phase_deadline": room["phase_deadline"],
        "phase_kind": room["phase_kind"],
        "settings": GAME_SETTINGS.copy(),
    }


def instructor_payload():
    payload = {}
    for room_id, room in rooms.items():
        payload[room_id] = {
            "state": room["state"],
            "round": room["round"],
            "word": room["word"],
            "player_count": active_player_count(room),
            "private_room": room["private_room"],
            "archived": bool(room.get("archived")),
            "archived_at": room.get("archived_at"),
            "retention_deadline": room.get("retention_deadline"),
            "clues_committed": len([sid for sid in room["clues"] if room["players"].get(sid, {}).get("active")]),
            "revealed_clues": room["revealed_clues"],
            "current_turn_name": room["players"][active_turn_sid(room)]["name"]
            if active_turn_sid(room)
            else None,
            "game_over": room["game_over"],
            "players": [
                {
                    "name": player["name"],
                    "connected": player["connected"],
                    "active": player["active"],
                    "is_insider": sid == room["insider_sid"],
                    "has_voted": sid in room["votes"],
                    "has_committed_clue": sid in room["clues"],
                    "is_agent": player["is_agent"],
                    "role": player["role"],
                    "status_reason": player["status_reason"],
                }
                for sid, player in room["players"].items()
            ],
            "result": room["result"],
        }
    return payload


def emit_instructor_update():
    socketio.emit(
        "instructor_update",
        {"rooms": instructor_payload(), "settings": GAME_SETTINGS.copy()},
        to=INSTRUCTOR_DASHBOARD_ROOM,
    )


def broadcast_room_state(room_id):
    if room_id not in rooms:
        emit_instructor_update()
        return
    socketio.emit("room_update", room_payload(room_id), to=room_id)
    emit_instructor_update()


def reset_round(room):
    room["state"] = "lobby"
    room["word"] = None
    room["votes"] = {}
    room["result"] = None
    room["game_over"] = False
    room["clues"] = {}
    room["revealed_clues"] = []
    room["reveal_queue"] = []
    room["turn_order"] = []
    room["current_turn_index"] = 0
    room["phase_deadline"] = None
    room["phase_kind"] = None
    room["phase_turn_sid"] = None
    for player in room["players"].values():
        if player["active"]:
            player["role"] = None
            if player["status_reason"] == "eliminated":
                player["status_reason"] = None
        player["agent_memory"] = {}


def can_start_next_round(room):
    return room["state"] == "results" and room["result"] and not room["game_over"]


def insider_survival_threshold_reached(room, active_ids=None):
    contenders = active_ids if active_ids is not None else active_player_ids(room)
    return room["insider_sid"] in contenders and len(contenders) <= 3


def agent_count_for_room(room):
    if not GAME_SETTINGS["agents_enabled"]:
        return 0
    target_size = min(RECOMMENDED_GROUP_SIZE, ROOM_MAX_SIZE)
    missing = max(0, target_size - active_player_count(room))
    return missing


def add_agents_to_room(room):
    existing_names = {player["name"] for player in room["players"].values()}
    for _ in range(agent_count_for_room(room)):
        available = [name for name in AGENT_NAMES if name not in existing_names]
        name = random.choice(available or AGENT_NAMES)
        agent_sid = f"agent-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        room["players"][agent_sid] = create_player(name, is_agent=True)
        existing_names.add(name)


def normalized(text):
    return text.strip().casefold()


def clue_bank_for_word(word):
    bank = AGENT_CLUE_BANK.get(word, [])
    pieces = [piece.casefold() for piece in word.replace("-", " ").split()]
    return list(dict.fromkeys([clue.casefold() for clue in bank] + pieces))


def clue_matches_secret_word(word, clue):
    return normalized(clue) == normalized(word)


def agent_loyal_clue(word, used_clues):
    candidates = AGENT_CLUE_BANK.get(word, [])
    available = [
        clue
        for clue in candidates
        if normalized(clue) not in used_clues and not clue_matches_secret_word(word, clue)
    ]
    if available:
        return random.choice(available)
    for token in word.replace("-", " ").split():
        if normalized(token) not in used_clues and not clue_matches_secret_word(word, token):
            return token.lower()
    generic_choices = [clue for clue in GENERIC_CLUES if not clue_matches_secret_word(word, clue)]
    return random.choice(generic_choices or GENERIC_CLUES)


def agent_insider_clue(room):
    context = normalized(GAME_SETTINGS["context"])
    context_hint = None
    for token in ("trust", "money", "security", "network", "group", "secret"):
        if token in context:
            context_hint = token
            break

    existing = [entry["clue"] for entry in room["revealed_clues"]]
    generic_pool = list(dict.fromkeys(existing + GENERIC_CLUES))
    if context_hint:
        generic_pool.insert(0, context_hint)
    valid_generic = [
        clue for clue in GENERIC_CLUES if not clue_matches_secret_word(room["word"], clue)
    ]
    valid_pool = [
        clue for clue in generic_pool if not clue_matches_secret_word(room["word"], clue)
    ]
    return random.choice(valid_pool or valid_generic or ["signal"])


def commit_clue(room, sid, clue):
    room["clues"][sid] = clue


def clue_already_used(room, clue):
    clue_key = normalized(clue)
    return any(normalized(existing) == clue_key for existing in room["clues"].values())


def name_already_used(room, candidate_name):
    candidate_key = normalized_name(candidate_name)
    return any(normalized_name(player["name"]) == candidate_key for player in room["players"].values())


def process_agent_clues(room_id):
    room = rooms[room_id]
    used_clues = {normalized(clue) for clue in room["clues"].values()}

    for sid, player in room["players"].items():
        if not player["active"] or not player["is_agent"] or sid in room["clues"]:
            continue
        if sid == room["insider_sid"]:
            clue = agent_insider_clue(room)
        else:
            clue = agent_loyal_clue(room["word"], used_clues)
        commit_clue(room, sid, clue)
        used_clues.add(normalized(clue))


def maybe_finish_clue_phase(room_id):
    room = rooms[room_id]
    if GAME_SETTINGS["reveal_mode"] != "simultaneous":
        return
    if len(room["clues"]) != active_player_count(room):
        return

    clue_entries = [
        {"player_name": room["players"][sid]["name"], "clue": clue, "player_id": sid}
        for sid, clue in room["clues"].items()
    ]

    room["revealed_clues"] = clue_entries
    room["state"] = "vote"
    start_phase_timer(room_id, "vote")


def active_turn_sid(room):
    if room["state"] != "clue" or GAME_SETTINGS["reveal_mode"] != "random":
        return None
    if room["current_turn_index"] >= len(room["turn_order"]):
        return None
    sid = room["turn_order"][room["current_turn_index"]]
    if not room["players"].get(sid, {}).get("active"):
        return None
    return sid


def advance_turn(room_id):
    room = rooms[room_id]
    room["current_turn_index"] += 1
    process_random_sequence_turns(room_id)


def record_sequential_clue(room, sid, clue):
    commit_clue(room, sid, clue)
    room["revealed_clues"].append(
        {"player_name": room["players"][sid]["name"], "clue": clue, "player_id": sid}
    )


def process_random_sequence_turns(room_id):
    room = rooms[room_id]
    while room["current_turn_index"] < len(room["turn_order"]):
        sid = room["turn_order"][room["current_turn_index"]]
        player = room["players"].get(sid)
        if not player:
            room["current_turn_index"] += 1
            continue
        if not player["active"]:
            room["current_turn_index"] += 1
            continue
        if sid in room["clues"]:
            room["current_turn_index"] += 1
            continue
        if not player["is_agent"]:
            start_phase_timer(room_id, "clue", sid)
            return

        used_clues = {normalized(clue) for clue in room["clues"].values()}
        if sid == room["insider_sid"]:
            clue = agent_insider_clue(room)
            if normalized(clue) in used_clues or clue_matches_secret_word(room["word"], clue):
                fallback_pool = [
                    item
                    for item in GENERIC_CLUES
                    if normalized(item) not in used_clues
                    and not clue_matches_secret_word(room["word"], item)
                ]
                clue = random.choice(fallback_pool or ["signal"])
        else:
            clue = agent_loyal_clue(room["word"], used_clues)

        record_sequential_clue(room, sid, clue)
        room["current_turn_index"] += 1

    room["state"] = "vote"
    start_phase_timer(room_id, "vote")


def clear_phase_timer(room):
    room["phase_deadline"] = None
    room["phase_kind"] = None
    room["phase_turn_sid"] = None


def start_phase_timer(room_id, phase_kind, turn_sid=None):
    room = rooms.get(room_id)
    if not room:
        return
    deadline = time.time() + action_timeout_seconds()
    room["phase_deadline"] = deadline
    room["phase_kind"] = phase_kind
    room["phase_turn_sid"] = turn_sid

    def monitor_phase_timeout():
        socketio.sleep(max(0, deadline - time.time()))
        active_room = rooms.get(room_id)
        if not active_room:
            return
        if active_room["phase_deadline"] != deadline:
            return
        if active_room["phase_kind"] != phase_kind:
            return
        if active_room["phase_turn_sid"] != turn_sid:
            return
        handle_phase_timeout(room_id, phase_kind, turn_sid)

    socketio.start_background_task(monitor_phase_timeout)


def eliminate_players(room_id, player_ids, reason):
    room = rooms.get(room_id)
    if not room:
        return
    for player_id in player_ids:
        eliminate_player(
            room_id,
            player_id,
            disconnected=False,
            timed_out=(reason == "timeout"),
            broadcast=False,
        )
    maybe_finish_round_after_elimination(room_id)
    broadcast_room_state(room_id)


def handle_phase_timeout(room_id, phase_kind, turn_sid=None):
    room = rooms.get(room_id)
    if not room:
        return

    if phase_kind == "clue":
        if GAME_SETTINGS["reveal_mode"] == "random":
            if room["state"] != "clue" or active_turn_sid(room) != turn_sid:
                return
            if turn_sid and turn_sid not in room["clues"] and room["players"].get(turn_sid, {}).get("active"):
                eliminate_players(room_id, [turn_sid], "timeout")
            return

        if room["state"] != "clue":
            return
        timed_out = [
            sid
            for sid in active_player_ids(room)
            if sid not in room["clues"]
        ]
        if timed_out:
            eliminate_players(room_id, timed_out, "timeout")
    elif phase_kind == "vote":
        if room["state"] != "vote":
            return
        timed_out = [
            sid
            for sid in active_player_ids(room)
            if sid not in room["votes"]
        ]
        if timed_out:
            eliminate_players(room_id, timed_out, "timeout")


def emit_role_to_player(room, player_id):
    player = room["players"][player_id]
    if player["is_agent"] or not player["sid"]:
        return
    if player_id == room["insider_sid"]:
        socketio.emit("role_assigned", {"role": "insider", "word": None}, to=player["sid"])
    else:
        socketio.emit(
            "role_assigned",
            {"role": "player", "word": room["word"]},
            to=player["sid"],
        )


def start_round(room_id):
    room = rooms[room_id]
    if room["round"] == 0:
        add_agents_to_room(room)
    contenders = active_player_ids(room)
    if not contenders:
        return False
    insider_sid = room["insider_sid"]
    if insider_sid is None:
        insider_sid = random.choice(contenders)
    elif insider_sid not in contenders:
        return False
    room["insider_sid"] = insider_sid
    room["roster_locked"] = True
    room["state"] = "clue"
    room["game_over"] = False
    room["round"] += 1
    room["word"] = random.choice(active_secret_words())
    room["votes"] = {}
    room["result"] = None
    room["clues"] = {}
    room["revealed_clues"] = []
    room["reveal_queue"] = []
    room["turn_order"] = []
    room["current_turn_index"] = 0
    clear_phase_timer(room)

    for sid, player in room["players"].items():
        if not player["active"]:
            continue
        player["role"] = "insider" if sid == room["insider_sid"] else "player"
        player["status_reason"] = None
        player["agent_memory"] = {"submitted_clue": False}
        emit_role_to_player(room, sid)

    if GAME_SETTINGS["reveal_mode"] == "simultaneous":
        process_agent_clues(room_id)
        maybe_finish_clue_phase(room_id)
        if room["state"] == "clue":
            start_phase_timer(room_id, "clue")
    else:
        room["turn_order"] = list(contenders)
        random.shuffle(room["turn_order"])
        process_random_sequence_turns(room_id)
    return True


def reveal_next_clue(room):
    if room["state"] != "reveal" or not room["reveal_queue"]:
        return False
    room["revealed_clues"].append(room["reveal_queue"].pop(0))
    if not room["reveal_queue"]:
        room["state"] = "vote"
    return True


def conclude_vote(room_id):
    room = rooms[room_id]
    clear_phase_timer(room)
    tally = {}
    for target_sid in room["votes"].values():
        tally[target_sid] = tally.get(target_sid, 0) + 1

    eliminated_sid = None
    if tally:
        top_votes = max(tally.values())
        leaders = [sid for sid, total in tally.items() if total == top_votes]
        if len(leaders) == 1:
            eliminated_sid = leaders[0]

    vote_summary = [
        {
            "voter_name": room["players"][voter_sid]["name"],
            "target_name": room["players"].get(target_sid, {}).get("name", "No vote"),
        }
        for voter_sid, target_sid in room["votes"].items()
    ]

    result = {
        "word": room["word"],
        "insider_name": room["players"].get(room["insider_sid"], {}).get("name", "Unknown"),
        "eliminated_name": room["players"].get(eliminated_sid, {}).get("name")
        if eliminated_sid
        else None,
        "vote_summary": vote_summary,
        "revealed_clues": room["revealed_clues"],
        "winner": None,
        "game_over": False,
        "message": None,
    }

    if eliminated_sid is None:
        room["state"] = "results"
        result["message"] = "The vote was tied, so nobody was eliminated. The game continues to another round."
    elif eliminated_sid == room["insider_sid"]:
        room["players"][eliminated_sid]["status_reason"] = "eliminated"
        room["state"] = "guess"
        result["message"] = (
            f"{result['eliminated_name']} was identified as the Insider. "
            "They get one final chance to guess the secret."
        )
    else:
        eliminate_player(room_id, eliminated_sid, broadcast=False)
        room["state"] = "results"
        if insider_survival_threshold_reached(room):
            result["winner"] = "insider"
            result["game_over"] = True
            result["message"] = (
                f"{result['eliminated_name']} was eliminated. "
                "Only three active players remain, so the Insider wins the game."
            )
        else:
            result["message"] = (
                f"{result['eliminated_name']} was eliminated. "
                "The game continues to another round."
            )

    room["result"] = result
    room["game_over"] = result["game_over"]


def conclude_round_after_insider_departure(room, departing_name):
    clear_phase_timer(room)
    room["state"] = "results"
    room["game_over"] = True
    room["result"] = {
        "word": room["word"],
        "insider_name": departing_name,
        "eliminated_name": departing_name,
        "vote_summary": room.get("result", {}).get("vote_summary", []),
        "revealed_clues": room["revealed_clues"],
        "winner": "group",
        "game_over": True,
        "message": f"{departing_name} was the Insider and disconnected, so the group wins the game.",
    }


def agent_guess_word(room):
    return random.choice(active_secret_words())


def genericity_score(clue):
    clue = normalized(clue)
    score = 0
    if clue in {normalized(item) for item in GENERIC_CLUES}:
        score += 3
    if len(clue) <= 4:
        score += 1
    return score


def agent_vote_target(room, sid):
    fallback = [target_sid for target_sid in active_player_ids(room) if target_sid != sid]
    if not fallback:
        return None

    expected = set(clue_bank_for_word(room["word"]))
    suspicion = []
    seen = {}
    for entry in room["revealed_clues"]:
        clue = normalized(entry["clue"])
        target_sid = entry["player_id"]
        if target_sid == sid:
            continue
        score = genericity_score(clue)
        if clue not in expected:
            score += 2
        if clue in seen:
            score += 1
        seen[clue] = seen.get(clue, 0) + 1
        suspicion.append((score, target_sid))

    suspicion.sort(reverse=True)
    if room["players"][sid]["role"] == "insider":
        non_self = [target_sid for _, target_sid in suspicion if target_sid != sid]
        strategic_target = random.choice(non_self or fallback)
    elif suspicion:
        strategic_target = suspicion[0][1]
    else:
        strategic_target = random.choice(fallback)

    if random.random() < 0.7:
        return strategic_target
    return random.choice(fallback)


def process_agent_votes(room):
    for sid, player in room["players"].items():
        if not player["active"] or not player["is_agent"] or sid in room["votes"]:
            continue
        target_sid = agent_vote_target(room, sid)
        if target_sid:
            room["votes"][sid] = target_sid


def vote_summary_for_room(room):
    return [
        {
            "voter_name": room["players"][voter_sid]["name"],
            "target_name": room["players"].get(target_sid, {}).get("name", "No vote"),
        }
        for voter_sid, target_sid in room["votes"].items()
    ]


def resolve_insider_guess(room_id, guess, was_caught=False):
    room = rooms[room_id]
    clear_phase_timer(room)
    existing_result = room.get("result") or {}
    room["state"] = "results"
    room["game_over"] = True
    room["result"] = {
        "word": room["word"],
        "insider_name": existing_result.get("insider_name")
        or room["players"].get(room["insider_sid"], {}).get("name", "Unknown"),
        "eliminated_name": existing_result.get("eliminated_name"),
        "vote_summary": existing_result.get("vote_summary") or vote_summary_for_room(room),
        "revealed_clues": existing_result.get("revealed_clues") or list(room["revealed_clues"]),
        "winner": None,
        "game_over": True,
        "message": None,
    }
    guessed_correctly = normalized(guess) == normalized(room["word"])
    room["result"]["final_guess"] = guess
    room["result"]["winner"] = "insider" if guessed_correctly else "group"
    room["result"]["message"] = (
        "The Insider guessed the word and stole the game."
        if guessed_correctly
        else (
            "The Insider missed the final guess, so the group wins."
            if was_caught
            else "The Insider guessed incorrectly, so the group wins."
        )
    )
    socketio.emit("game_over", room["result"], to=room_id)
    broadcast_room_state(room_id)


def finalize_agent_guess_if_needed(room_id):
    room = rooms[room_id]
    insider = room["players"].get(room["insider_sid"])
    if not insider or not insider["is_agent"]:
        return
    guess = agent_guess_word(room)
    resolve_insider_guess(room_id, guess, was_caught=True)


def cleanup_room(room_id):
    room = rooms.get(room_id)
    if not room or active_player_count(room):
        return
    if room.get("archived"):
        return
    if room["round"] == 0:
        rooms.pop(room_id, None)
        return
    archive_room(room_id)


def archive_room(room_id):
    room = rooms.get(room_id)
    if not room:
        return
    now = time.time()
    deadline = now + retention_minutes() * 60
    room["archived"] = True
    room["archived_at"] = now
    room["retention_deadline"] = deadline
    clear_phase_timer(room)

    def discard_after_retention():
        socketio.sleep(max(0, deadline - time.time()))
        current = rooms.get(room_id)
        if not current:
            return
        if not current.get("archived"):
            return
        if current.get("retention_deadline") != deadline:
            return
        rooms.pop(room_id, None)
        emit_instructor_update()

    socketio.start_background_task(discard_after_retention)


def schedule_disconnect_deadline(room_id, player_id, deadline):
    def monitor_disconnect():
        socketio.sleep(disconnect_grace_seconds())
        room = rooms.get(room_id)
        if not room or player_id not in room["players"]:
            return
        player = room["players"][player_id]
        if player["connected"] or player["disconnect_deadline"] != deadline:
            return
        eliminate_player(room_id, player_id, disconnected=True)

    socketio.start_background_task(monitor_disconnect)


def maybe_finish_round_after_elimination(room_id):
    room = rooms.get(room_id)
    if not room:
        return

    active_ids = active_player_ids(room)
    active_insider = room["insider_sid"] in active_ids

    if room["state"] in {"clue", "reveal", "vote", "guess"} and not active_insider:
        departing_name = room.get("result", {}).get("insider_name", "The Insider")
        conclude_round_after_insider_departure(room, departing_name)
        socketio.emit("game_over", room["result"], to=room_id)
        return
    if room["state"] in {"clue", "reveal", "vote"} and insider_survival_threshold_reached(room, active_ids):
        clear_phase_timer(room)
        room["state"] = "results"
        room["game_over"] = True
        room["result"] = {
            "word": room["word"],
            "insider_name": room["players"].get(room["insider_sid"], {}).get("name", "Unknown"),
            "eliminated_name": None,
            "vote_summary": room.get("result", {}).get("vote_summary", []),
            "revealed_clues": room["revealed_clues"],
            "winner": "insider",
            "game_over": True,
            "message": "Only three active players remain, so the Insider wins the game.",
        }
        socketio.emit("game_over", room["result"], to=room_id)
        return

    if room["state"] == "clue":
        if GAME_SETTINGS["reveal_mode"] == "simultaneous":
            maybe_finish_clue_phase(room_id)
        else:
            process_random_sequence_turns(room_id)
    elif room["state"] == "vote":
        if len(room["votes"]) == len(active_ids):
            conclude_vote(room_id)
            if room["state"] == "results" and room["game_over"]:
                socketio.emit("game_over", room["result"], to=room_id)
            elif room["state"] == "guess":
                socketio.emit("guess_prompt", room["result"], to=room_id)
                finalize_agent_guess_if_needed(room_id)
    elif room["state"] == "guess" and not active_insider:
        clear_phase_timer(room)
        room["state"] = "results"
        room["game_over"] = True
        room["result"]["winner"] = "group"
        room["result"]["game_over"] = True
        room["result"]["message"] = "The Insider disconnected before the final guess, so the group wins."
        socketio.emit("game_over", room["result"], to=room_id)


def eliminate_player(room_id, player_id, disconnected=False, timed_out=False, broadcast=True):
    room = rooms.get(room_id)
    if not room or player_id not in room["players"]:
        return

    player = room["players"][player_id]
    if not player["active"]:
        player["disconnect_deadline"] = None
        return
    old_sid = player.get("sid")
    if old_sid:
        sid_to_player.pop(old_sid, None)
        player_to_room.pop(old_sid, None)

    player["sid"] = None
    player["connected"] = False
    player["active"] = False
    player["disconnect_deadline"] = None
    departing_name = player["name"]
    was_insider = room["insider_sid"] == player_id
    if timed_out:
        player["status_reason"] = "timeout"
    elif disconnected:
        player["status_reason"] = "disconnected"
    else:
        player["status_reason"] = player["status_reason"] or "eliminated"
    room["votes"].pop(player_id, None)
    room["clues"].pop(player_id, None)
    room["reveal_queue"] = [
        entry for entry in room["reveal_queue"] if entry["player_id"] != player_id
    ]
    if player_id in room["turn_order"]:
        removed_index = room["turn_order"].index(player_id)
        room["turn_order"] = [entry for entry in room["turn_order"] if entry != player_id]
        if removed_index < room["current_turn_index"]:
            room["current_turn_index"] -= 1
        if room["current_turn_index"] >= len(room["turn_order"]):
            room["current_turn_index"] = len(room["turn_order"])
    for voter_sid, target_sid in list(room["votes"].items()):
        if target_sid == player_id:
            room["votes"].pop(voter_sid, None)

    if not active_player_count(room) and room["state"] in {"lobby", "results"}:
        cleanup_room(room_id)
        emit_instructor_update()
        return

    if (disconnected or timed_out) and room["state"] in {"clue", "vote", "guess"}:
        room["result"] = room.get("result") or {
            "word": room["word"],
            "insider_name": departing_name if was_insider else room["players"].get(room["insider_sid"], {}).get("name", departing_name),
            "revealed_clues": room["revealed_clues"],
            "vote_summary": [],
        }
        if timed_out:
            room["result"]["message"] = f"{departing_name} ran out of time and was removed from the round."
        else:
            room["result"]["message"] = f"{departing_name} disconnected and was removed after the grace period."

    if broadcast:
        maybe_finish_round_after_elimination(room_id)
        broadcast_room_state(room_id)


def remove_player_from_room(room_id, player_id):
    room = rooms.get(room_id)
    if not room or player_id not in room["players"]:
        return

    player = room["players"][player_id]
    old_sid = player.get("sid")
    if old_sid:
        sid_to_player.pop(old_sid, None)
        player_to_room.pop(old_sid, None)

    room["players"].pop(player_id, None)
    room["votes"].pop(player_id, None)
    room["clues"].pop(player_id, None)
    room["revealed_clues"] = [
        entry for entry in room["revealed_clues"] if entry["player_id"] != player_id
    ]
    room["reveal_queue"] = [
        entry for entry in room["reveal_queue"] if entry["player_id"] != player_id
    ]
    room["turn_order"] = [entry for entry in room["turn_order"] if entry != player_id]
    if room["current_turn_index"] > len(room["turn_order"]):
        room["current_turn_index"] = len(room["turn_order"])
    for voter_sid, target_sid in list(room["votes"].items()):
        if target_sid == player_id:
            room["votes"].pop(voter_sid, None)

    if not active_player_count(room):
        cleanup_room(room_id)
        emit_instructor_update()
        return

    if not room["players"]:
        cleanup_room(room_id)
        emit_instructor_update()
        return

    broadcast_room_state(room_id)


def handle_disconnect_grace(sid):
    room_id, player_id = detach_socket(sid)
    if not room_id or room_id not in rooms or not player_id:
        return

    room = rooms[room_id]
    if player_id not in room["players"]:
        return

    player = room["players"][player_id]
    if player["is_agent"]:
        return

    player["connected"] = False
    player["sid"] = None
    deadline = time.time() + disconnect_grace_seconds()
    player["disconnect_deadline"] = deadline
    schedule_disconnect_deadline(room_id, player_id, deadline)
    broadcast_room_state(room_id)


@app.route("/")
def index():
    requested_room = (request.args.get("room") or "").strip().upper()
    requested_player_token = (request.args.get("player") or "").strip()
    script_root = request.script_root or ""
    return render_template(
        "index.html",
        room_min_size=ROOM_MIN_SIZE,
        room_max_size=ROOM_MAX_SIZE,
        recommended_group_size=RECOMMENDED_GROUP_SIZE,
        socketio_client_url=url_for("static", filename="vendor/socket.io.min.js"),
        socketio_path=f"{script_root}/socket.io" if script_root else "/socket.io",
        script_root=script_root,
        requested_room=requested_room,
        requested_player_token=requested_player_token,
        current_private_rooms_enabled=GAME_SETTINGS["private_rooms_enabled"],
        current_game_enabled=GAME_SETTINGS["game_enabled"],
    )


@app.route("/instructor")
@requires_auth
def instructor():
    script_root = request.script_root or ""
    return render_template(
        "instructor.html",
        room_max_size=ROOM_MAX_SIZE,
        socketio_client_url=url_for("static", filename="vendor/socket.io.min.js"),
        socketio_path=f"{script_root}/socket.io" if script_root else "/socket.io",
        student_url=url_for("index"),
    )


@app.route("/room/<room_id>/qr.png")
def room_qr(room_id):
    join_url = url_for("index", room=room_id.strip().upper(), _external=True)
    image = qrcode.make(join_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")


@socketio.on("join")
def handle_join(data):
    room_id, existing_room = current_room()
    if existing_room:
        emit("joined", {"room_id": room_id, "sid": current_player_id(), "player_token": current_player_id()})
        emit("room_update", room_payload(room_id))
        return

    name = (data.get("name") or "").strip()
    join_mode = data.get("join_mode") or "open"
    requested_room_value = data.get("room_id")
    requested_room_lookup = (requested_room_value or "").strip().upper()
    requested_room_id = get_requested_room(requested_room_value)
    player_token = (data.get("player_token") or "").strip()

    if player_token and requested_room_lookup and requested_room_lookup in rooms:
        room = rooms[requested_room_lookup]
        if player_token in room["players"] and room["players"][player_token]["active"]:
            join_room(requested_room_lookup)
            attach_socket_to_player(requested_room_lookup, player_token, request.sid)
            emit("joined", {"room_id": requested_room_lookup, "sid": player_token, "player_token": player_token})
            if room["state"] in {"clue", "vote", "guess", "results"}:
                emit_role_to_player(room, player_token)
            broadcast_room_state(requested_room_lookup)
            return
        if player_token in room["players"] and not room["players"][player_token]["active"]:
            emit("error_message", {"message": "That seat is no longer active in this game."})
            return

    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction. Please wait for the instructor to reopen it."})
        return
    if not name:
        emit("error_message", {"message": "Please enter your name before joining."})
        return
    if requested_room_value and not requested_room_id:
        emit("error_message", {"message": "That room is unavailable. Ask the host for a fresh join link."})
        return

    if join_mode == "create_private":
        if not GAME_SETTINGS["private_rooms_enabled"]:
            emit("error_message", {"message": "Private rooms are disabled by the instructor."})
            return
        room_id = create_room(private_room=True)
    elif join_mode == "join_private":
        if not GAME_SETTINGS["private_rooms_enabled"]:
            emit("error_message", {"message": "Private rooms are disabled by the instructor."})
            return
        if not requested_room_id:
            emit("error_message", {"message": "Enter a valid private room code."})
            return
        if not rooms[requested_room_id]["private_room"]:
            emit("error_message", {"message": "That room is not a private game."})
            return
        room_id = requested_room_id
    elif join_mode == "room_link":
        if not requested_room_id:
            emit("error_message", {"message": "That room is unavailable. Ask the host for a fresh join link."})
            return
        room_id = requested_room_id
    else:
        room_id = get_or_create_room()

    room = rooms[room_id]
    if room["state"] != "lobby" or active_player_count(room) >= ROOM_MAX_SIZE:
        emit("error_message", {"message": "That room filled up. Please try again."})
        return
    if room["roster_locked"]:
        emit("error_message", {"message": "That game is already in progress and its roster is locked."})
        return
    if name_already_used(room, name):
        emit("error_message", {"message": "That name is already in use in this room. Choose a different one."})
        return

    join_room(room_id)
    player_id = generate_player_id()
    room["players"][player_id] = create_player(name[:40])
    attach_socket_to_player(room_id, player_id, request.sid)

    emit("joined", {"room_id": room_id, "sid": player_id, "player_token": player_id})
    broadcast_room_state(room_id)


@socketio.on("submit_clue")
def handle_submit_clue(data):
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or room["state"] != "clue":
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return

    clue = (data.get("clue") or "").strip()
    if not clue:
        emit("error_message", {"message": "Enter a one-word clue before submitting."})
        return
    if " " in clue.strip():
        emit("error_message", {"message": "Use a single clue word."})
        return
    if player_id in room["clues"]:
        emit("error_message", {"message": "You already locked in your clue."})
        return
    if clue_matches_secret_word(room["word"], clue):
        emit("error_message", {"message": "You cannot use the secret word itself as your clue."})
        return
    if clue_already_used(room, clue):
        emit("error_message", {"message": "Use a different clue than the ones already submitted."})
        return
    if GAME_SETTINGS["reveal_mode"] == "random" and player_id != active_turn_sid(room):
        emit("error_message", {"message": "Wait for your turn before submitting a clue."})
        return

    clue = clue[:30]
    if GAME_SETTINGS["reveal_mode"] == "simultaneous":
        commit_clue(room, player_id, clue)
        process_agent_clues(room_id)
        maybe_finish_clue_phase(room_id)
    else:
        record_sequential_clue(room, player_id, clue)
        advance_turn(room_id)
    broadcast_room_state(room_id)


@socketio.on("start_game")
def handle_start_game():
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or not player_id:
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return
    if room["state"] != "lobby":
        emit("error_message", {"message": "This room is already mid-round."})
        return

    projected_size = active_player_count(room) + agent_count_for_room(room)
    if projected_size < ROOM_MIN_SIZE:
        emit(
            "error_message",
            {"message": f"You need at least {ROOM_MIN_SIZE} total players before starting."},
        )
        return

    start_round(room_id)
    broadcast_room_state(room_id)


@socketio.on("reveal_next")
def handle_reveal_next():
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or not player_id or room["state"] != "reveal":
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return
    if not reveal_next_clue(room):
        emit("error_message", {"message": "There are no clues left to reveal."})
        return
    broadcast_room_state(room_id)


@socketio.on("submit_vote")
def handle_submit_vote(data):
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or room["state"] != "vote":
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return

    target_sid = data.get("target_sid")
    if target_sid not in room["players"] or not room["players"][target_sid]["active"]:
        emit("error_message", {"message": "That vote target is no longer in the room."})
        return
    if target_sid == player_id:
        emit("error_message", {"message": "You cannot vote for yourself."})
        return

    room["votes"][player_id] = target_sid
    process_agent_votes(room)
    if len(room["votes"]) == active_player_count(room):
        conclude_vote(room_id)
        if room["state"] == "results" and room["game_over"]:
            socketio.emit("game_over", room["result"], to=room_id)
        elif room["state"] == "guess":
            socketio.emit("guess_prompt", room["result"], to=room_id)
            finalize_agent_guess_if_needed(room_id)

    broadcast_room_state(room_id)


@socketio.on("submit_guess")
def handle_submit_guess(data):
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or room["state"] not in {"clue", "reveal", "vote", "guess"}:
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return
    if player_id != room["insider_sid"]:
        emit("error_message", {"message": "Only the Insider can guess the secret word."})
        return
    if player_id not in room["players"] or not room["players"][player_id]["active"]:
        emit("error_message", {"message": "Your seat is no longer active in this game."})
        return

    guess = (data.get("guess") or "").strip()
    if not guess:
        emit("error_message", {"message": "Enter a guess before submitting."})
        return

    resolve_insider_guess(room_id, guess, was_caught=(room["state"] == "guess"))


def handle_start_next_round_request():
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or not player_id:
        return
    if not game_is_online():
        emit("error_message", {"message": "The game is currently offline during instruction."})
        return
    if not can_start_next_round(room):
        emit("error_message", {"message": "This game is not waiting to begin the next round."})
        return

    reset_round(room)
    if not start_round(room_id):
        emit("error_message", {"message": "The next round could not be started."})
        broadcast_room_state(room_id)
        return
    broadcast_room_state(room_id)


@socketio.on("start_next_round")
def handle_start_next_round():
    handle_start_next_round_request()


@socketio.on("leave_game")
def handle_leave_game():
    room_id, room = current_room()
    player_id = current_player_id()
    if not room or not player_id:
        return

    emit("left_game")
    leave_room(room_id)
    remove_player_from_room(room_id, player_id)


@socketio.on("update_settings")
def handle_update_settings(data):
    if not session.get("is_instructor"):
        emit("error_message", {"message": "Instructor authentication required."})
        return

    game_enabled = bool(data.get("game_enabled", True))
    disconnect_seconds = int(data.get("disconnect_grace_seconds", GAME_SETTINGS["disconnect_grace_seconds"]))
    action_timeout = int(data.get("action_timeout_seconds", GAME_SETTINGS["action_timeout_seconds"]))
    retention_value = int(data.get("retention_minutes", GAME_SETTINGS["retention_minutes"]))
    agents_enabled = bool(data.get("agents_enabled", GAME_SETTINGS["agents_enabled"]))
    private_rooms_enabled = bool(data.get("private_rooms_enabled", GAME_SETTINGS["private_rooms_enabled"]))
    reveal_mode = data.get("reveal_mode", GAME_SETTINGS["reveal_mode"])
    context = (data.get("context") or "").strip()
    custom_words = (data.get("custom_words") or "").strip()

    if disconnect_seconds < 0 or disconnect_seconds > 120:
        emit("error_message", {"message": "Disconnect grace must be between 0 and 120 seconds."})
        return
    if action_timeout < 15 or action_timeout > 300:
        emit("error_message", {"message": "Action timeout must be between 15 and 300 seconds."})
        return
    if retention_value < MIN_RETENTION_MINUTES or retention_value > MAX_RETENTION_MINUTES:
        emit(
            "error_message",
            {"message": f"Game retention must be between {MIN_RETENTION_MINUTES} and {MAX_RETENTION_MINUTES} minutes."},
        )
        return
    if reveal_mode not in {"simultaneous", "random"}:
        emit("error_message", {"message": "Unsupported reveal mode."})
        return

    GAME_SETTINGS["game_enabled"] = game_enabled
    GAME_SETTINGS["disconnect_grace_seconds"] = disconnect_seconds
    GAME_SETTINGS["action_timeout_seconds"] = action_timeout
    GAME_SETTINGS["retention_minutes"] = retention_value
    GAME_SETTINGS["agents_enabled"] = agents_enabled
    GAME_SETTINGS["private_rooms_enabled"] = private_rooms_enabled
    GAME_SETTINGS["reveal_mode"] = reveal_mode
    GAME_SETTINGS["context"] = context
    GAME_SETTINGS["custom_words"] = custom_words
    emit_instructor_update()
    socketio.emit("settings_updated", GAME_SETTINGS.copy())


@socketio.on("advance_room")
def handle_advance_room(data):
    if not session.get("is_instructor"):
        emit("error_message", {"message": "Instructor authentication required."})
        return

    room_id = data.get("room_id")
    room = rooms.get(room_id)
    if not room or room["state"] != "reveal":
        emit("error_message", {"message": "That room is not waiting on a reveal."})
        return

    reveal_next_clue(room)
    broadcast_room_state(room_id)


@socketio.on("instructor_join")
def handle_instructor_join():
    if not session.get("is_instructor"):
        emit("error_message", {"message": "Instructor authentication required."})
        return
    join_room(INSTRUCTOR_DASHBOARD_ROOM)
    emit("instructor_update", {"rooms": instructor_payload(), "settings": GAME_SETTINGS.copy()})


@socketio.on("disconnect")
def handle_disconnect():
    leave_room(INSTRUCTOR_DASHBOARD_ROOM)
    handle_disconnect_grace(request.sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
