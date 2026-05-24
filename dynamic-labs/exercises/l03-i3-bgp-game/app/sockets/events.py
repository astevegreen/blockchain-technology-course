from __future__ import annotations

from typing import Any

from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from ..state.game_state import PHASE_DEBRIEF, PHASE_TALLY, PHASE_WAITING_DEBRIEF, game_state


INSTRUCTOR_ROOM = "instructors"


def register_socket_events(socketio: SocketIO) -> None:
    def emit_dashboard_state() -> None:
        socketio.emit("dashboard_state", game_state.serialize_dashboard_state(), to=INSTRUCTOR_ROOM)

    def emit_student_state(uuid: str, event_name: str = "state_snapshot") -> None:
        sid = game_state.uuid_to_sid.get(uuid)
        if sid:
            socketio.emit(event_name, game_state.serialize_student_state(uuid), to=sid)

    def emit_room_states(room_id: str, event_name: str = "room_update") -> None:
        room = game_state.rooms[room_id]
        for uuid in room.human_player_ids():
            emit_student_state(uuid, event_name)

    def emit_error(message: str) -> None:
        emit("server_error", {"message": message})

    def instructor_only() -> bool:
        if session.get("is_instructor"):
            return True
        emit_error("Instructor authentication is required for this action.")
        return False

    def reveal_room_to_students_and_instructor(room_id: str) -> bool:
        try:
            debrief = game_state.reveal_debrief(room_id)
        except ValueError as exc:
            emit_error(str(exc))
            return False
        socketio.emit("debrief_ready", debrief, to=INSTRUCTOR_ROOM)
        emit_room_states(room_id, "debrief_ready")
        emit_dashboard_state()
        return True

    def lobby_timeout_monitor() -> None:
        while True:
            socketio.sleep(5)
            removed = game_state.prune_inactive_lobby_players()
            if removed:
                emit_dashboard_state()

    @socketio.on("connect")
    def handle_connect():
        emit("connected", {"sid": request.sid})

    @socketio.on("join_instructor")
    def handle_join_instructor():
        if not instructor_only():
            return
        game_state.add_instructor_sid(request.sid)
        join_room(INSTRUCTOR_ROOM)
        emit("dashboard_state", game_state.serialize_dashboard_state())

    @socketio.on("register")
    def handle_register(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = (payload.get("uuid") or "").strip()
        lobby_mode = payload.get("mode", "collab")
        if not uuid:
            emit_error("Missing player UUID.")
            return
        if lobby_mode == "single" and not game_state.settings.self_service_enabled:
            lobby_mode = "collab"

        player, _ = game_state.register_player(uuid, request.sid, lobby_mode=lobby_mode)
        if player.room_id:
            join_room(player.room_id)
        emit("restore_state", game_state.serialize_student_state(uuid))
        emit_dashboard_state()

    @socketio.on("preview_rooms")
    def handle_preview_rooms(payload: dict[str, Any] | None):
        if not instructor_only():
            return
        payload = payload or {}
        mode = payload.get("mode", "collab")
        room_size = int(payload.get("room_size", 8))
        try:
            preview = game_state.preview_rooms(mode=mode, room_size=room_size)
        except ValueError as exc:
            emit_error(str(exc))
            return
        emit("room_preview", {"mode": mode, "room_size": room_size, "rooms": preview})

    @socketio.on("launch_game")
    def handle_launch_game(payload: dict[str, Any] | None):
        if not instructor_only():
            return
        payload = payload or {}
        mode = payload.get("mode", "collab")
        room_configs = payload.get("rooms", [])
        if not room_configs:
            emit_error("Generate room previews before launching the simulation.")
            return
        try:
            launched_rooms = game_state.launch_rooms(mode=mode, room_configs=room_configs)
        except ValueError as exc:
            emit_error(str(exc))
            return

        for room in launched_rooms:
            for uuid in room.human_player_ids():
                sid = game_state.uuid_to_sid.get(uuid)
                if sid:
                    join_room(room.room_id, sid=sid)
            if room.session_started:
                game_state.execute_bot_turn(room.room_id)
                game_state.move_room_to_tally_if_ready(room.room_id)
            emit_room_states(room.room_id, "phase_1_start")

        emit("launch_result", {"launched_rooms": [room.room_id for room in launched_rooms]})
        emit_dashboard_state()

    @socketio.on("submit_broadcast")
    def handle_submit_broadcast(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        player = game_state.get_player(uuid)
        if not player or (player.origin == "human" and player.is_bot):
            emit_error("A bot is currently controlling this node.")
            return
        try:
            room = game_state.apply_broadcast(uuid, payload.get("messages", {}))
        except ValueError as exc:
            emit_error(str(exc))
            return

        advanced = game_state.move_room_to_tally_if_ready(room.room_id)
        if advanced:
            emit_room_states(room.room_id, "phase_2_start")
        else:
            emit_room_states(room.room_id, "room_update")
        emit_dashboard_state()

    @socketio.on("create_single_player_room")
    def handle_create_single_player_room(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        conflict = game_state.active_self_service_room_conflict(uuid)
        if conflict and not payload.get("abandon_existing"):
            emit("self_service_room_conflict", conflict)
            return
        try:
            if conflict and payload.get("abandon_existing"):
                game_state.abandon_self_service_room(uuid)
            size = int(payload.get("size", 8))
            num_traitors = int(payload.get("num_traitors", 0))
            room = game_state.create_single_player_room_for_player(uuid, size=size, num_traitors=num_traitors)
        except (TypeError, ValueError) as exc:
            emit_error(str(exc))
            return

        join_room(room.room_id)
        emit_student_state(uuid, "phase_1_start")
        emit_dashboard_state()

    @socketio.on("submit_final_vote")
    def handle_submit_final_vote(payload: dict[str, Any] | None):
        payload = payload or {}
        uuid = game_state.sid_to_uuid.get(request.sid)
        if not uuid:
            emit_error("Player session not registered.")
            return
        player = game_state.get_player(uuid)
        if not player or (player.origin == "human" and player.is_bot):
            emit_error("A bot is currently controlling this node.")
            return
        try:
            room = game_state.submit_final_vote(uuid, payload.get("value"))
        except ValueError as exc:
            emit_error(str(exc))
            return

        emit_room_states(room.room_id, "room_update")
        emit_dashboard_state()

    @socketio.on("force_takeover")
    def handle_force_takeover(payload: dict[str, Any] | None):
        if not instructor_only():
            return
        payload = payload or {}
        room_id = payload.get("room_id")
        target_uuid = payload.get("target_uuid")
        if room_id not in game_state.rooms:
            emit_error("Room not found.")
            return
        if not target_uuid:
            emit_error("Select a specific node to take over.")
            return
        previous_phase = game_state.rooms[room_id].phase
        try:
            takeover_result = game_state.force_takeover(room_id, target_uuid)
        except ValueError as exc:
            emit_error(str(exc))
            return
        room = game_state.rooms[room_id]
        event_name = "room_update"
        if previous_phase != PHASE_TALLY and room.phase == PHASE_TALLY:
            event_name = "phase_2_start"
        emit_room_states(room_id, event_name)
        emit("force_takeover_result", takeover_result)
        emit_dashboard_state()

    @socketio.on("toggle_self_service")
    def handle_toggle_self_service(payload: dict[str, Any] | None):
        if not instructor_only():
            return
        payload = payload or {}
        enabled = bool(payload.get("enabled", False))
        game_state.settings.self_service_enabled = enabled
        emit("self_service_toggled", {"self_service_enabled": enabled})
        emit_dashboard_state()

    @socketio.on("reveal_debrief")
    def handle_reveal_debrief(payload: dict[str, Any] | None):
        if not instructor_only():
            return
        payload = payload or {}
        room_id = payload.get("room_id")
        if room_id not in game_state.rooms:
            emit_error("Room not found.")
            return
        reveal_room_to_students_and_instructor(room_id)

    @socketio.on("request_room_debrief")
    def handle_request_room_debrief(payload: dict[str, Any] | None):
        payload = payload or {}
        room_id = payload.get("room_id")
        if room_id not in game_state.rooms:
            emit_error("Room not found.")
            return
        room = game_state.rooms[room_id]
        if not room.debrief_revealed:
            emit_error("The instructor has not revealed this debrief yet.")
            return
        requester_uuid = game_state.sid_to_uuid.get(request.sid)
        if not session.get("is_instructor") and requester_uuid not in room.players:
            emit_error("You are not assigned to this room.")
            return
        emit("debrief_ready", game_state.build_debrief_payload(room_id))

    @socketio.on("reveal_room_debrief")
    def handle_reveal_room_debrief():
        requester_uuid = game_state.sid_to_uuid.get(request.sid)
        if not requester_uuid:
            emit_error("Player session not registered.")
            return
        player = game_state.get_player(requester_uuid)
        if not player or not player.room_id:
            emit_error("Player is not assigned to a room.")
            return
        room = game_state.rooms[player.room_id]
        if player.origin != "human":
            emit_error("Only human students can reveal a room debrief.")
            return
        if room.phase not in (PHASE_WAITING_DEBRIEF, PHASE_DEBRIEF):
            emit_error("The debrief is not ready yet.")
            return
        reveal_room_to_students_and_instructor(room.room_id)

    @socketio.on("restart_to_lobby")
    def handle_restart_to_lobby(payload: dict[str, Any] | None):
        payload = payload or {}
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
            game_state.restart_player_to_lobby(uuid, lobby_mode=payload.get("mode", "collab"))
        except ValueError as exc:
            emit_error(str(exc))
            return

        leave_room(previous_room_id)
        emit_student_state(uuid, "restore_state")
        emit_dashboard_state()

    @socketio.on("disconnect")
    def handle_disconnect():
        player = game_state.mark_disconnect(request.sid)
        game_state.remove_instructor_sid(request.sid)
        if player and player.room_id and player.room_id in game_state.rooms:
            takeover = game_state.disconnect_takeover(player.uuid)
            event_name = "room_update"
            if takeover:
                room = game_state.rooms.get(player.room_id)
                if room and room.phase == 2:
                    event_name = "phase_2_start"
            emit_room_states(player.room_id, event_name)
        emit_dashboard_state()

    socketio.start_background_task(lobby_timeout_monitor)
