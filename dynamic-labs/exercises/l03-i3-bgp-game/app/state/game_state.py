from __future__ import annotations

import random
import string
import time
from dataclasses import dataclass, field
from typing import Any


ATTACK = "Attack"
RETREAT = "Retreat"
VALUES = (ATTACK, RETREAT)
NODE_IDS = list(string.ascii_uppercase)
LOBBY_INACTIVE_TIMEOUT_SECONDS = 60
UNCERTAIN_FLIP_PERCENT = 50

PHASE_QUEUE = 0
PHASE_BROADCAST = 1
PHASE_TALLY = 2
PHASE_WAITING_DEBRIEF = 3
PHASE_DEBRIEF = 4

PHASE_LABELS = {
    PHASE_QUEUE: "Queue",
    PHASE_BROADCAST: "Broadcast",
    PHASE_TALLY: "Tally",
    PHASE_WAITING_DEBRIEF: "Awaiting Debrief",
    PHASE_DEBRIEF: "Debrief",
}


@dataclass
class BroadcastRecord:
    sender_uuid: str
    sender_node_id: str
    recipient_uuid: str
    recipient_node_id: str
    value: str
    sender_role: str
    via_bot: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class Player:
    uuid: str
    label: str
    sid: str | None = None
    lobby_mode: str = "collab"
    room_id: str | None = None
    node_id: str | None = None
    role: str = "honest"
    initial_value: str = ATTACK
    uncertainty_seed: int | None = None
    inbox: dict[str, str] = field(default_factory=dict)
    final_vote: str | None = None
    is_bot: bool = False
    origin: str = "human"
    connected: bool = False
    has_broadcast: bool = False
    broadcast_payload: dict[str, str] = field(default_factory=dict)
    was_taken_over: bool = False
    was_disconnect_takeover: bool = False
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def reset_for_room(self, room_id: str) -> None:
        self.room_id = room_id
        self.node_id = None
        self.role = "honest"
        self.initial_value = ATTACK
        self.uncertainty_seed = None
        self.inbox = {}
        self.final_vote = None
        self.has_broadcast = False
        self.broadcast_payload = {}
        self.was_taken_over = False
        self.was_disconnect_takeover = False
        if self.origin == "human":
            self.is_bot = False

    def actor_kind(self) -> str:
        if self.origin == "bot":
            return "bot"
        if self.was_taken_over:
            return "taken_over"
        return "human"


@dataclass
class Room:
    room_id: str
    mode: str
    phase: int
    size: int
    num_traitors: int
    initial_order: str = ATTACK
    session_started: bool = True
    players: dict[str, Player] = field(default_factory=dict)
    ordered_player_ids: list[str] = field(default_factory=list)
    broadcast_log: list[BroadcastRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    debrief_revealed: bool = False

    def phase_label(self) -> str:
        return PHASE_LABELS[self.phase]

    def display_phase_label(self) -> str:
        return self.phase_label()

    def human_player_ids(self) -> list[str]:
        return [player_id for player_id in self.ordered_player_ids if self.players[player_id].origin == "human"]

    def bot_player_ids(self) -> list[str]:
        return [player_id for player_id in self.ordered_player_ids if self.players[player_id].origin == "bot"]


@dataclass
class Settings:
    self_service_enabled: bool = False


@dataclass
class GameState:
    queue: list[str] = field(default_factory=list)
    rooms: dict[str, Room] = field(default_factory=dict)
    players: dict[str, Player] = field(default_factory=dict)
    uuid_to_sid: dict[str, str] = field(default_factory=dict)
    sid_to_uuid: dict[str, str] = field(default_factory=dict)
    instructor_sids: set[str] = field(default_factory=set)
    next_student_number: int = 1
    next_room_number: int = 1
    settings: Settings = field(default_factory=Settings)
    random_seed: int = field(default_factory=lambda: int(time.time() * 1000))
    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.random_seed)
        print(f"[bgp-game] random seed: {self.random_seed}", flush=True)

    def next_uncertainty_seed(self, used_seeds: set[int]) -> int:
        while True:
            candidate = self.rng.randrange(0, 2**31)
            if candidate not in used_seeds:
                used_seeds.add(candidate)
                return candidate

    def register_player(self, uuid: str, sid: str, lobby_mode: str = "collab") -> tuple[Player, bool]:
        self.prune_inactive_lobby_players()
        is_new = uuid not in self.players
        if is_new:
            player = Player(uuid=uuid, label=f"Student {self.next_student_number}")
            self.next_student_number += 1
            self.players[uuid] = player
        player = self.players[uuid]
        if player.sid and player.sid != sid:
            self.sid_to_uuid.pop(player.sid, None)
        player.sid = sid
        player.connected = True
        player.last_seen = time.time()
        player.lobby_mode = "single" if lobby_mode == "single" else "collab"
        self.uuid_to_sid[uuid] = sid
        self.sid_to_uuid[sid] = uuid
        if player.room_id is None:
            if player.lobby_mode == "single":
                self.remove_player_from_queue(uuid)
            else:
                self.add_player_to_queue(uuid)
        return player, is_new

    def mark_disconnect(self, sid: str) -> Player | None:
        uuid = self.sid_to_uuid.pop(sid, None)
        if not uuid:
            self.instructor_sids.discard(sid)
            return None
        player = self.players.get(uuid)
        if player:
            if player.sid and player.sid != sid:
                return player
            player.connected = False
            player.sid = None
            player.last_seen = time.time()
        if self.uuid_to_sid.get(uuid) == sid:
            self.uuid_to_sid.pop(uuid, None)
        return player

    def disconnect_takeover(self, uuid: str) -> dict | None:
        """
        Called after mark_disconnect. If the player was in an active room and
        still has pending phase actions, immediately hand the node to bot control
        and advance the room if all remaining actions are now resolved.
        Returns a result dict (same shape as force_takeover) if any action was
        taken, or None if no takeover was needed.
        """
        player = self.players.get(uuid)
        if not player or not player.room_id:
            return None
        room = self.rooms.get(player.room_id)
        if not room:
            return None
        if player.origin != "human" or player.is_bot:
            return None

        acted = False
        if room.phase == PHASE_BROADCAST and not player.has_broadcast:
            player.is_bot = True
            player.was_disconnect_takeover = True
            self.execute_bot_turn(room.room_id, player_ids=[uuid])
            self.move_room_to_tally_if_ready(room.room_id)
            acted = True
        elif room.phase == PHASE_TALLY and player.final_vote is None:
            player.is_bot = True
            player.was_disconnect_takeover = True
            self.execute_bot_votes(room.room_id, player_ids=[uuid])
            if all(room.players[pid].final_vote for pid in room.ordered_player_ids):
                room.phase = PHASE_WAITING_DEBRIEF
            acted = True

        if not acted:
            return None

        return {
            "room_id": room.room_id,
            "uuid": uuid,
            "node_id": player.node_id,
            "phase": room.phase,
        }

    def add_instructor_sid(self, sid: str) -> None:
        self.instructor_sids.add(sid)

    def remove_instructor_sid(self, sid: str) -> None:
        self.instructor_sids.discard(sid)

    def add_player_to_queue(self, uuid: str) -> None:
        if uuid not in self.players:
            return
        player = self.players[uuid]
        if player.room_id is not None:
            return
        if uuid not in self.queue:
            self.queue.append(uuid)

    def remove_player_from_queue(self, uuid: str) -> None:
        self.queue = [player_uuid for player_uuid in self.queue if player_uuid != uuid]

    def prune_inactive_lobby_players(self, timeout_seconds: int = LOBBY_INACTIVE_TIMEOUT_SECONDS) -> list[str]:
        cutoff = time.time() - timeout_seconds
        removed: list[str] = []
        for uuid in list(self.queue):
            player = self.players.get(uuid)
            if not player:
                self.remove_player_from_queue(uuid)
                removed.append(uuid)
                continue
            if player.room_id is None and not player.connected and player.last_seen <= cutoff:
                self.remove_player_from_queue(uuid)
                removed.append(uuid)
        return removed

    def queue_position(self, uuid: str) -> int | None:
        try:
            return self.queue.index(uuid) + 1
        except ValueError:
            return None

    def generate_room_id(self) -> str:
        room_id = f"BGP-{self.next_room_number:04d}"
        self.next_room_number += 1
        return room_id

    def preview_rooms(self, mode: str, room_size: int) -> list[dict[str, Any]]:
        self.prune_inactive_lobby_players()
        if mode != "collab":
            raise ValueError("The instructor dashboard can only preview collaborative rooms.")
        room_size = max(1, min(room_size, len(NODE_IDS)))
        queued = [uuid for uuid in self.queue if uuid in self.players and self.players[uuid].room_id is None]
        previews: list[dict[str, Any]] = []

        chunks = [queued[index : index + room_size] for index in range(0, len(queued), room_size)]
        for index, chunk in enumerate(chunks, start=1):
            if not chunk:
                continue
            human_count = len(chunk)
            default_bots = max(room_size - human_count, 0)
            actual_size = human_count + default_bots
            previews.append(
                {
                    "preview_id": f"preview-{index}",
                    "room_label": f"Room {index}",
                    "mode": mode,
                    "human_count": human_count,
                    "bot_count": default_bots,
                    "size": actual_size,
                    "max_bots": len(NODE_IDS) - human_count,
                    "participant_uuids": chunk,
                    "participant_labels": [self.players[uuid].label for uuid in chunk],
                    "default_traitors": self.default_traitor_count(actual_size),
                }
            )
        return previews

    def default_traitor_count(self, room_size: int) -> int:
        if room_size < 4:
            return 0
        return max(1, min(room_size - 1, (room_size - 1) // 3))

    def create_room(self, mode: str, participant_uuids: list[str], size: int, num_traitors: int) -> Room:
        if size < 1 or size > len(NODE_IDS):
            raise ValueError("Room size must be between 1 and 26.")
        if not participant_uuids:
            raise ValueError("Cannot create a room without participants.")
        if size < len(participant_uuids):
            raise ValueError("Room size cannot be smaller than the number of human participants.")
        for uuid in participant_uuids:
            player = self.players.get(uuid)
            if not player or player.room_id is not None:
                raise ValueError("Preview is stale. Regenerate room assignments and try again.")
            if mode != "single" and uuid not in self.queue:
                raise ValueError("Preview is stale. Regenerate room assignments and try again.")

        room_id = self.generate_room_id()
        room = Room(
            room_id=room_id,
            mode=mode,
            phase=PHASE_BROADCAST,
            size=size,
            num_traitors=num_traitors,
            initial_order=self.rng.choice(VALUES),
            session_started=True,
        )
        self.rooms[room_id] = room

        ordered_player_ids: list[str] = []
        for uuid in participant_uuids:
            player = self.players.get(uuid)
            self.remove_player_from_queue(uuid)
            player.reset_for_room(room_id)
            player.connected = player.sid is not None
            room.players[uuid] = player
            ordered_player_ids.append(uuid)

        if mode == "single" and len(participant_uuids) != 1:
            raise ValueError("Single player rooms require exactly one human participant.")

        bot_slots = size - len(participant_uuids)
        if bot_slots:
            for index in range(bot_slots):
                bot_uuid = f"{room_id}-bot-{index + 1}-{self.rng.randrange(0x10000):04x}"
                bot_player = Player(
                    uuid=bot_uuid,
                    label=f"Bot {index + 1}",
                    room_id=room_id,
                    is_bot=True,
                    origin="bot",
                    connected=False,
                )
                bot_player.reset_for_room(room_id)
                bot_player.is_bot = True
                bot_player.connected = False
                self.players[bot_uuid] = bot_player
                room.players[bot_uuid] = bot_player
                ordered_player_ids.append(bot_uuid)

        room.ordered_player_ids = ordered_player_ids
        for index, uuid in enumerate(room.ordered_player_ids):
            player = room.players[uuid]
            player.node_id = NODE_IDS[index]
            if player.origin == "bot":
                player.label = f"Bot {player.node_id}"

        role_targets = set(self.rng.sample(room.ordered_player_ids, k=min(num_traitors, len(room.ordered_player_ids))))
        used_uncertainty_seeds: set[int] = set()
        for uuid in room.ordered_player_ids:
            player = room.players[uuid]
            player.role = "traitor" if uuid in role_targets else "honest"
            player.initial_value = room.initial_order
            player.uncertainty_seed = self.next_uncertainty_seed(used_uncertainty_seeds)

        return room

    def launch_rooms(self, mode: str, room_configs: list[dict[str, Any]]) -> list[Room]:
        if mode != "collab":
            raise ValueError("The instructor dashboard can only launch collaborative rooms.")
        launched_rooms: list[Room] = []
        for config in room_configs:
            participant_uuids = config.get("participant_uuids", [])
            size = int(config.get("size", len(participant_uuids)))
            num_traitors = int(config.get("num_traitors", 0))
            if num_traitors < 0 or num_traitors >= size:
                raise ValueError("Malicious node count must be between 0 and room size minus 1.")
            launched_rooms.append(
                self.create_room(mode=mode, participant_uuids=participant_uuids, size=size, num_traitors=num_traitors)
            )
        return launched_rooms

    def create_single_player_room_for_player(self, uuid: str, size: int, num_traitors: int) -> Room:
        self.prune_inactive_lobby_players()
        if not self.settings.self_service_enabled:
            raise ValueError("Self-Service Mode is currently disabled by the instructor.")
        player = self.players.get(uuid)
        if not player:
            raise ValueError("Player session not registered.")
        if player.room_id is not None:
            raise ValueError("You are already assigned to a room.")
        if player.lobby_mode != "single":
            raise ValueError("Switch to Self-Service Mode before creating a room.")

        if num_traitors < 0 or num_traitors >= size:
            raise ValueError("Malicious node count must be between 0 and room size minus 1.")
        room = self.create_room(mode="single", participant_uuids=[uuid], size=size, num_traitors=num_traitors)
        self.execute_bot_turn(room.room_id)
        self.move_room_to_tally_if_ready(room.room_id)
        return room

    def active_self_service_room_conflict(self, uuid: str) -> dict[str, Any] | None:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            return None
        room = self.rooms.get(player.room_id)
        if not room or room.mode != "single" or player.origin != "human":
            return None
        return {
            "room_id": room.room_id,
            "phase": room.phase,
            "phase_label": room.display_phase_label(),
            "size": room.size,
            "num_traitors": room.num_traitors,
        }

    def abandon_self_service_room(self, uuid: str) -> dict[str, Any]:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("You do not have an active self-service room.")
        room = self.rooms.get(player.room_id)
        if not room or room.mode != "single":
            raise ValueError("Only active self-service rooms can be abandoned.")
        if player.origin != "human":
            raise ValueError("Only the human self-service participant can abandon this room.")

        room_id = room.room_id
        for participant_uuid in list(room.ordered_player_ids):
            participant = room.players[participant_uuid]
            if participant.origin == "bot":
                self.players.pop(participant_uuid, None)
                continue
            participant.room_id = None
            participant.node_id = None
            participant.role = "honest"
            participant.initial_value = ATTACK
            participant.inbox = {}
            participant.final_vote = None
            participant.has_broadcast = False
            participant.broadcast_payload = {}
            participant.is_bot = False
            participant.was_taken_over = False
            participant.was_disconnect_takeover = False
        self.rooms.pop(room_id, None)
        return {"room_id": room_id}

    def restart_player_to_lobby(self, uuid: str, lobby_mode: str = "collab") -> Player:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("You are not currently assigned to a completed room.")
        room = self.rooms.get(player.room_id)
        if not room or room.phase != PHASE_DEBRIEF:
            raise ValueError("Start Over is only available after the debrief is revealed.")

        normalized_mode = "single" if lobby_mode == "single" and self.settings.self_service_enabled else "collab"
        refreshed_player = Player(
            uuid=player.uuid,
            label=player.label,
            sid=player.sid,
            lobby_mode=normalized_mode,
            connected=player.connected,
        )
        refreshed_player.last_seen = time.time()
        self.players[uuid] = refreshed_player
        if refreshed_player.sid:
            self.uuid_to_sid[uuid] = refreshed_player.sid
            self.sid_to_uuid[refreshed_player.sid] = uuid

        self.remove_player_from_queue(uuid)
        if normalized_mode == "collab":
            self.add_player_to_queue(uuid)
        return refreshed_player

    def get_player(self, uuid: str) -> Player | None:
        return self.players.get(uuid)

    def get_room_for_player(self, uuid: str) -> Room | None:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            return None
        return self.rooms.get(player.room_id)

    def apply_broadcast(self, uuid: str, payload: dict[str, str], via_bot: bool = False) -> Room:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("Player is not assigned to a room.")
        room = self.rooms[player.room_id]
        if room.phase != PHASE_BROADCAST:
            raise ValueError("Broadcasts are closed for this room.")
        if player.has_broadcast:
            raise ValueError("Broadcast already submitted.")

        messages: dict[str, str] = {}
        for target_uuid in room.ordered_player_ids:
            if target_uuid == uuid:
                continue
            target_node_id = room.players[target_uuid].node_id
            if player.role == "honest":
                value = player.initial_value
            else:
                value = payload.get(target_node_id)
                if value not in VALUES:
                    raise ValueError("Malicious node payload must include Attack or Retreat for every peer.")
            messages[target_node_id] = value

        for target_uuid in room.ordered_player_ids:
            if target_uuid == uuid:
                continue
            recipient = room.players[target_uuid]
            value = messages[recipient.node_id]
            recipient.inbox[player.node_id] = value
            room.broadcast_log.append(
                BroadcastRecord(
                    sender_uuid=player.uuid,
                    sender_node_id=player.node_id or "?",
                    recipient_uuid=recipient.uuid,
                    recipient_node_id=recipient.node_id or "?",
                    value=value,
                    sender_role=player.role,
                    via_bot=via_bot,
                )
            )

        player.broadcast_payload = messages
        player.has_broadcast = True
        return room

    def execute_bot_turn(self, room_id: str, player_ids: list[str] | None = None) -> list[str]:
        room = self.rooms[room_id]
        acted: list[str] = []
        candidate_ids = player_ids or room.ordered_player_ids
        dishonest_value = self.malicious_room_vote(room)
        for uuid in candidate_ids:
            player = room.players[uuid]
            if not player.is_bot or player.has_broadcast:
                continue
            payload: dict[str, str] = {}
            for target_uuid in room.ordered_player_ids:
                if target_uuid == uuid:
                    continue
                target_node_id = room.players[target_uuid].node_id
                if player.role == "honest":
                    payload[target_node_id] = player.initial_value
                else:
                    payload[target_node_id] = dishonest_value
            self.apply_broadcast(uuid, payload, via_bot=True)
            acted.append(uuid)
        return acted

    def move_room_to_tally_if_ready(self, room_id: str) -> bool:
        room = self.rooms[room_id]
        if room.phase != PHASE_BROADCAST:
            return False
        if all(room.players[uuid].has_broadcast for uuid in room.ordered_player_ids):
            room.phase = PHASE_TALLY
            self.execute_bot_votes(room_id)
            if all(room.players[uuid].final_vote for uuid in room.ordered_player_ids):
                room.phase = PHASE_WAITING_DEBRIEF
            return True
        return False

    def submit_final_vote(self, uuid: str, value: str) -> Room:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("Player is not assigned to a room.")
        room = self.rooms[player.room_id]
        if room.phase != PHASE_TALLY:
            raise ValueError("Final voting is not open for this room.")
        if player.final_vote is not None:
            raise ValueError("Final vote already submitted.")
        if value not in VALUES:
            raise ValueError("Final vote must be Attack or Retreat.")
        if player.origin == "human" and not player.is_bot and player.role == "honest":
            if not self.player_has_consensus_tie(player):
                expected_value = self.player_consensus_vote(player)
                if value != expected_value:
                    raise ValueError(f"Final vote must match your node's local consensus: {expected_value}.")
        player.final_vote = value
        if all(room.players[player_id].final_vote for player_id in room.ordered_player_ids):
            room.phase = PHASE_WAITING_DEBRIEF
        return room

    def execute_bot_votes(self, room_id: str, player_ids: list[str] | None = None) -> list[str]:
        room = self.rooms[room_id]
        voted: list[str] = []
        candidate_ids = player_ids or room.ordered_player_ids
        for uuid in candidate_ids:
            player = room.players[uuid]
            if not player.is_bot or player.final_vote is not None:
                continue
            player.final_vote = self.determine_bot_vote(room, player)
            voted.append(uuid)
        return voted

    def determine_bot_vote(self, room: Room, player: Player) -> str:
        if player.role == "honest":
            return self.compute_local_consensus(player)
        return self.malicious_room_vote(room)

    def force_takeover(self, room_id: str, target_uuid: str) -> dict[str, Any]:
        room = self.rooms[room_id]
        if room.phase not in (PHASE_BROADCAST, PHASE_TALLY):
            raise ValueError("No takeover action is available in this phase.")
        if target_uuid not in room.players:
            raise ValueError("Selected node is not in this room.")

        player = room.players[target_uuid]
        if player.origin != "human":
            raise ValueError("Only human-origin nodes can be taken over.")
        if player.is_bot:
            raise ValueError("This node is already bot-controlled.")
        if not player.connected:
            raise ValueError("This node is no longer connected.")

        if room.phase == PHASE_BROADCAST:
            if player.has_broadcast:
                raise ValueError("This node has already completed broadcast.")
            player.is_bot = True
            player.was_taken_over = True
            self.execute_bot_turn(room_id, player_ids=[target_uuid])
            self.move_room_to_tally_if_ready(room_id)
        else:
            if player.final_vote is not None:
                raise ValueError("This node has already submitted a final vote.")
            player.is_bot = True
            player.was_taken_over = True
            self.execute_bot_votes(room_id, player_ids=[target_uuid])
            if all(room.players[player_id].final_vote for player_id in room.ordered_player_ids):
                room.phase = PHASE_WAITING_DEBRIEF
        return {
            "room_id": room_id,
            "taken_over": [player.node_id],
            "target_uuid": target_uuid,
            "phase": room.phase,
        }

    def reveal_debrief(self, room_id: str) -> dict[str, Any]:
        room = self.rooms[room_id]
        if room.phase not in (PHASE_WAITING_DEBRIEF, PHASE_DEBRIEF):
            raise ValueError("The debrief is not ready yet.")
        if room.debrief_revealed:
            return self.build_debrief_payload(room_id)
        room.debrief_revealed = True
        room.phase = PHASE_DEBRIEF
        return self.build_debrief_payload(room_id)

    def compute_majority(self, values: list[str]) -> str:
        attack_votes = sum(1 for value in values if value == ATTACK)
        retreat_votes = sum(1 for value in values if value == RETREAT)
        if attack_votes > retreat_votes:
            return ATTACK
        return RETREAT

    def local_vote_counts(self, player: Player) -> tuple[int, int]:
        values = list(player.inbox.values())
        attack_votes = sum(1 for value in values if value == ATTACK)
        retreat_votes = sum(1 for value in values if value == RETREAT)
        return attack_votes, retreat_votes

    def player_has_consensus_tie(self, player: Player) -> bool:
        attack_votes, retreat_votes = self.local_vote_counts(player)
        return attack_votes == retreat_votes

    def seeded_tie_break_vote(self, player: Player) -> str:
        seed_value = player.uncertainty_seed or 0
        should_flip = seed_value % 100 < UNCERTAIN_FLIP_PERCENT
        if should_flip:
            return RETREAT if player.initial_value == ATTACK else ATTACK
        return player.initial_value

    def compute_local_consensus(self, player: Player) -> str:
        attack_votes, retreat_votes = self.local_vote_counts(player)
        if attack_votes > retreat_votes:
            return ATTACK
        if retreat_votes > attack_votes:
            return RETREAT
        return self.seeded_tie_break_vote(player)

    def player_consensus_vote(self, player: Player) -> str:
        return self.compute_local_consensus(player)

    def correct_consensus(self, room: Room) -> str:
        honest_values = [
            room.players[player_id].initial_value
            for player_id in room.ordered_player_ids
            if room.players[player_id].role == "honest"
        ]
        return self.compute_majority(honest_values)

    def malicious_room_vote(self, room: Room) -> str:
        honest_consensus = self.correct_consensus(room)
        return RETREAT if honest_consensus == ATTACK else ATTACK

    def build_debrief_payload(self, room_id: str) -> dict[str, Any]:
        room = self.rooms[room_id]
        correct_consensus = self.correct_consensus(room)
        players = []
        for uuid in room.ordered_player_ids:
            player = room.players[uuid]
            local_tie = self.player_has_consensus_tie(player)
            local_consensus = self.player_consensus_vote(player)
            if local_tie and player.origin == "human" and not player.is_bot:
                local_consensus = "Tie"
            survived = player.role == "traitor" or player.final_vote == correct_consensus
            players.append(
                {
                    "uuid": player.uuid,
                    "label": player.label,
                    "node_id": player.node_id,
                    "role": player.role,
                    "origin": player.origin,
                    "initial_value": player.initial_value,
                    "local_consensus": local_consensus,
                    "local_tie": local_tie,
                    "final_vote": player.final_vote,
                    "is_bot": player.is_bot,
                    "was_taken_over": player.was_taken_over,
                    "was_disconnect_takeover": player.was_disconnect_takeover,
                    "survived": survived,
                }
            )

        edges = [
            {
                "from": record.sender_node_id,
                "to": record.recipient_node_id,
                "value": record.value,
                "sender_role": record.sender_role,
                "via_bot": record.via_bot,
            }
            for record in room.broadcast_log
        ]

        return {
            "room_id": room.room_id,
            "mode": room.mode,
            "phase": room.phase,
            "phase_label": room.display_phase_label(),
            "size": room.size,
            "num_traitors": room.num_traitors,
            "correct_consensus": correct_consensus,
            "players": players,
            "edges": edges,
        }

    def serialize_student_state(self, uuid: str) -> dict[str, Any]:
        self.prune_inactive_lobby_players()
        player = self.players[uuid]
        room = self.get_room_for_player(uuid)
        if room is None:
            return {
                "view": "queue",
                "player": {
                    "uuid": player.uuid,
                    "label": player.label,
                    "connected": player.connected,
                    "lobby_mode": player.lobby_mode,
                },
                "queue_count": len(self.queue),
                "queue_position": self.queue_position(uuid),
                "settings": {
                    "self_service_enabled": self.settings.self_service_enabled,
                },
            }

        control_locked = player.origin == "human" and player.is_bot
        if room.phase == PHASE_BROADCAST:
            view = "broadcast_wait" if player.has_broadcast or control_locked else "broadcast"
        elif room.phase == PHASE_TALLY:
            view = "tally_wait" if player.final_vote or control_locked else "tally"
        elif room.phase == PHASE_WAITING_DEBRIEF:
            view = "await_debrief"
        else:
            view = "debrief"

        peer_nodes = [
            {
                "uuid": peer.uuid,
                "label": peer.label,
                "node_id": peer.node_id,
            }
            for peer_id in room.ordered_player_ids
            if peer_id != uuid
            for peer in [room.players[peer_id]]
        ]

        return {
            "view": view,
            "player": {
                "uuid": player.uuid,
                "label": player.label,
                "node_id": player.node_id,
                "role": player.role,
                "initial_value": player.initial_value,
                "uncertainty_seed": player.uncertainty_seed,
                "final_vote": player.final_vote,
                "has_broadcast": player.has_broadcast,
                "is_bot": player.is_bot,
                "was_taken_over": player.was_taken_over,
                "origin": player.origin,
                "lobby_mode": player.lobby_mode,
            },
            "room": {
                "room_id": room.room_id,
                "mode": room.mode,
                "phase": room.phase,
                "phase_label": room.display_phase_label(),
                "session_started": room.session_started,
                "size": room.size,
                "num_traitors": room.num_traitors,
                "peer_nodes": peer_nodes,
                "player_nodes": [room.players[player_id].node_id for player_id in room.ordered_player_ids],
                "broadcast_complete": sum(1 for player_id in room.ordered_player_ids if room.players[player_id].has_broadcast),
                "vote_complete": sum(1 for player_id in room.ordered_player_ids if room.players[player_id].final_vote),
                "total_players": len(room.ordered_player_ids),
            },
            "messages": [
                {"sender": sender_node_id, "value": value}
                for sender_node_id, value in sorted(player.inbox.items())
            ],
            "control_locked": control_locked,
            "debrief": self.build_debrief_payload(room.room_id) if room.debrief_revealed else None,
        }

    def serialize_dashboard_state(self) -> dict[str, Any]:
        self.prune_inactive_lobby_players()
        rooms_payload = []
        for room_id in sorted(self.rooms.keys()):
            room = self.rooms[room_id]
            rooms_payload.append(
                {
                    "room_id": room.room_id,
                    "mode": room.mode,
                    "phase": room.phase,
                    "phase_label": room.display_phase_label(),
                    "session_started": room.session_started,
                    "size": room.size,
                    "num_traitors": room.num_traitors,
                    "debrief_revealed": room.debrief_revealed,
                    "broadcast_complete": sum(1 for player_id in room.ordered_player_ids if room.players[player_id].has_broadcast),
                    "vote_complete": sum(1 for player_id in room.ordered_player_ids if room.players[player_id].final_vote),
                    "total_players": len(room.ordered_player_ids),
                    "players": [
                        {
                            "uuid": room.players[player_id].uuid,
                            "label": room.players[player_id].label,
                            "node_id": room.players[player_id].node_id,
                            "role": room.players[player_id].role if room.phase >= PHASE_DEBRIEF else None,
                            "initial_value": room.players[player_id].initial_value if room.phase >= PHASE_DEBRIEF else None,
                            "final_vote": room.players[player_id].final_vote,
                            "connected": room.players[player_id].connected,
                            "is_bot": room.players[player_id].is_bot,
                            "origin": room.players[player_id].origin,
                            "was_taken_over": room.players[player_id].was_taken_over,
                            "has_broadcast": room.players[player_id].has_broadcast,
                        }
                        for player_id in room.ordered_player_ids
                    ],
                    "debrief": self.build_debrief_payload(room.room_id) if room.debrief_revealed else None,
                }
            )

        queued_players = [
            {
                "uuid": uuid,
                "label": self.players[uuid].label,
                "connected": self.players[uuid].connected,
            }
            for uuid in self.queue
            if uuid in self.players
        ]
        return {
            "queue_count": len(self.queue),
            "queue_players": queued_players,
            "rooms": rooms_payload,
            "settings": {
                "self_service_enabled": self.settings.self_service_enabled,
            },
        }


game_state = GameState()
