from __future__ import annotations

from typing import Any

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from ..state.game_state import PHASE_DEBRIEF, PHASE_WAITING_DEBRIEF, game_state


def register_socket_events(socketio: SocketIO) -> None:
    def emit_student_state(uuid: str, event_name: str = "state_snapshot") -> None:
        sid = game_state.uuid_to_sid.get(uuid)
        if sid:
            socketio.emit(event_name, game_state.serialize_student_state(uuid), to=sid)

    def emit_error(message: str) -> None:
        emit("server_error", {"message": message})

    @socketio.on("connect")
    def handle_connect():
        emit("connected", {"sid": request.sid})

    @socketio.on("register")
    def handle_register(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = (payload.get("uuid") or "").strip()
        if not uuid:
            emit_error("Missing player UUID.")
            return

        player, _ = game_state.register_player(uuid, request.sid)
        if player.room_id:
            join_room(player.room_id)
        emit("restore_state", game_state.serialize_student_state(uuid))

    @socketio.on("create_room")
    def handle_create_room(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        existing = game_state.active_room_summary(uuid)
        if existing and not payload.get("abandon_existing"):
            emit("room_conflict", existing)
            return
        try:
            if existing and payload.get("abandon_existing"):
                game_state.abandon_room(uuid)
            size = int(payload.get("size", 8))
            num_traitors = int(payload.get("num_traitors", 0))
            room = game_state.create_self_service_room(uuid, size=size, num_traitors=num_traitors)
        except (TypeError, ValueError) as exc:
            emit_error(str(exc))
            return

        join_room(room.room_id)
        emit_student_state(uuid, "phase_1_start")

    @socketio.on("submit_broadcast")
    def handle_submit_broadcast(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        try:
            room = game_state.apply_broadcast(uuid, payload.get("messages", {}))
        except ValueError as exc:
            emit_error(str(exc))
            return

        advanced = game_state.move_room_to_tally_if_ready(room.room_id)
        emit_student_state(uuid, "phase_2_start" if advanced else "room_update")

    @socketio.on("submit_final_vote")
    def handle_submit_final_vote(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        try:
            game_state.submit_final_vote(uuid, payload.get("value"))
        except ValueError as exc:
            emit_error(str(exc))
            return
        emit_student_state(uuid, "room_update")

    @socketio.on("reveal_room_debrief")
    def handle_reveal_room_debrief():
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        player = game_state.get_player(uuid)
        if not player or not player.room_id:
            emit_error("Player is not assigned to a room.")
            return
        room = game_state.rooms[player.room_id]
        if room.phase not in (PHASE_WAITING_DEBRIEF, PHASE_DEBRIEF):
            emit_error("The debrief is not ready yet.")
            return
        try:
            game_state.reveal_debrief(room.room_id)
        except ValueError as exc:
            emit_error(str(exc))
            return
        emit_student_state(uuid, "debrief_ready")

    @socketio.on("restart_to_lobby")
    def handle_restart_to_lobby():
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        player = game_state.get_player(uuid)
        if not player or not player.room_id:
            emit_error("You are not currently assigned to a completed room.")
            return
        previous_room_id = player.room_id
        try:
            game_state.restart_player_to_lobby(uuid)
        except ValueError as exc:
            emit_error(str(exc))
            return
        leave_room(previous_room_id)
        emit_student_state(uuid, "restore_state")

    @socketio.on("disconnect")
    def handle_disconnect():
        game_state.mark_disconnect(request.sid)
