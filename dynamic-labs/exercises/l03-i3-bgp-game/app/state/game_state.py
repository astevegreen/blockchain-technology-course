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
UNCERTAIN_FLIP_PERCENT = 50

PHASE_BROADCAST = 1
PHASE_TALLY = 2
PHASE_WAITING_DEBRIEF = 3
PHASE_DEBRIEF = 4

PHASE_LABELS = {
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
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


@dataclass
class Room:
    room_id: str
    phase: int
    size: int
    num_traitors: int
    initial_order: str = ATTACK
    players: dict[str, Player] = field(default_factory=dict)
    ordered_player_ids: list[str] = field(default_factory=list)
    broadcast_log: list[BroadcastRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    debrief_revealed: bool = False

    def phase_label(self) -> str:
        return PHASE_LABELS[self.phase]


@dataclass
class GameState:
    rooms: dict[str, Room] = field(default_factory=dict)
    players: dict[str, Player] = field(default_factory=dict)
    uuid_to_sid: dict[str, str] = field(default_factory=dict)
    sid_to_uuid: dict[str, str] = field(default_factory=dict)
    next_student_number: int = 1
    next_room_number: int = 1
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

    def register_player(self, uuid: str, sid: str) -> tuple[Player, bool]:
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
        self.uuid_to_sid[uuid] = sid
        self.sid_to_uuid[sid] = uuid
        return player, is_new

    def mark_disconnect(self, sid: str) -> Player | None:
        uuid = self.sid_to_uuid.pop(sid, None)
        if not uuid:
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

    def generate_room_id(self) -> str:
        room_id = f"BGP-{self.next_room_number:04d}"
        self.next_room_number += 1
        return room_id

    def default_traitor_count(self, room_size: int) -> int:
        if room_size < 4:
            return 0
        return max(1, min(room_size - 1, (room_size - 1) // 3))

    def create_self_service_room(self, uuid: str, size: int, num_traitors: int) -> Room:
        player = self.players.get(uuid)
        if not player:
            raise ValueError("Player session not registered.")
        if player.room_id is not None:
            raise ValueError("You are already assigned to a room.")
        if size < 1 or size > len(NODE_IDS):
            raise ValueError(f"Room size must be between 1 and {len(NODE_IDS)}.")
        if num_traitors < 0 or num_traitors >= size:
            raise ValueError("Malicious node count must be between 0 and room size minus 1.")

        room_id = self.generate_room_id()
        room = Room(
            room_id=room_id,
            phase=PHASE_BROADCAST,
            size=size,
            num_traitors=num_traitors,
            initial_order=self.rng.choice(VALUES),
        )
        self.rooms[room_id] = room

        ordered_player_ids: list[str] = [uuid]
        player.room_id = room_id
        player.node_id = None
        player.role = "honest"
        player.initial_value = ATTACK
        player.uncertainty_seed = None
        player.inbox = {}
        player.final_vote = None
        player.has_broadcast = False
        player.broadcast_payload = {}
        player.is_bot = False
        room.players[uuid] = player

        bot_slots = size - 1
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
            self.players[bot_uuid] = bot_player
            room.players[bot_uuid] = bot_player
            ordered_player_ids.append(bot_uuid)

        room.ordered_player_ids = ordered_player_ids
        for index, member_uuid in enumerate(room.ordered_player_ids):
            member = room.players[member_uuid]
            member.node_id = NODE_IDS[index]
            if member.origin == "bot":
                member.label = f"Bot {member.node_id}"

        role_targets = set(self.rng.sample(room.ordered_player_ids, k=min(num_traitors, len(room.ordered_player_ids))))
        used_uncertainty_seeds: set[int] = set()
        for member_uuid in room.ordered_player_ids:
            member = room.players[member_uuid]
            member.role = "traitor" if member_uuid in role_targets else "honest"
            member.initial_value = room.initial_order
            member.uncertainty_seed = self.next_uncertainty_seed(used_uncertainty_seeds)

        self.execute_bot_turn(room.room_id)
        self.move_room_to_tally_if_ready(room.room_id)
        return room

    def abandon_room(self, uuid: str) -> dict[str, Any]:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("You do not have an active room.")
        room = self.rooms.get(player.room_id)
        if not room:
            raise ValueError("Room not found.")

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
        self.rooms.pop(room_id, None)
        return {"room_id": room_id}

    def active_room_summary(self, uuid: str) -> dict[str, Any] | None:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            return None
        room = self.rooms.get(player.room_id)
        if not room:
            return None
        return {
            "room_id": room.room_id,
            "phase": room.phase,
            "phase_label": room.phase_label(),
            "size": room.size,
            "num_traitors": room.num_traitors,
        }

    def restart_player_to_lobby(self, uuid: str) -> Player:
        player = self.players.get(uuid)
        if not player or not player.room_id:
            raise ValueError("You are not currently assigned to a completed room.")
        room = self.rooms.get(player.room_id)
        if not room or room.phase != PHASE_DEBRIEF:
            raise ValueError("Start Over is only available after the debrief is revealed.")

        self.abandon_room(uuid)
        return self.players[uuid]

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

    def execute_bot_turn(self, room_id: str) -> list[str]:
        room = self.rooms[room_id]
        acted: list[str] = []
        dishonest_value = self.malicious_room_vote(room)
        for uuid in room.ordered_player_ids:
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
        if player.origin == "human" and player.role == "honest":
            if not self.player_has_consensus_tie(player):
                expected_value = self.player_consensus_vote(player)
                if value != expected_value:
                    raise ValueError(f"Final vote must match your node's local consensus: {expected_value}.")
        player.final_vote = value
        if all(room.players[player_id].final_vote for player_id in room.ordered_player_ids):
            room.phase = PHASE_WAITING_DEBRIEF
        return room

    def execute_bot_votes(self, room_id: str) -> list[str]:
        room = self.rooms[room_id]
        voted: list[str] = []
        for uuid in room.ordered_player_ids:
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
            if local_tie and player.origin == "human":
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
            "phase": room.phase,
            "phase_label": room.phase_label(),
            "size": room.size,
            "num_traitors": room.num_traitors,
            "correct_consensus": correct_consensus,
            "players": players,
            "edges": edges,
        }

    def serialize_student_state(self, uuid: str) -> dict[str, Any]:
        player = self.players[uuid]
        room = self.get_room_for_player(uuid)
        if room is None:
            return {
                "view": "lobby",
                "player": {
                    "uuid": player.uuid,
                    "label": player.label,
                    "connected": player.connected,
                },
            }

        if room.phase == PHASE_BROADCAST:
            view = "broadcast_wait" if player.has_broadcast else "broadcast"
        elif room.phase == PHASE_TALLY:
            view = "tally_wait" if player.final_vote else "tally"
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
                "origin": player.origin,
            },
            "room": {
                "room_id": room.room_id,
                "phase": room.phase,
                "phase_label": room.phase_label(),
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
            "debrief": self.build_debrief_payload(room.room_id) if room.debrief_revealed else None,
        }


game_state = GameState()
