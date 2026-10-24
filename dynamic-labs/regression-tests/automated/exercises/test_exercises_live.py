from __future__ import annotations

import unittest
import uuid as uuid_lib

from live_support import (
    DEFAULT_BASE_URL,
    SocketHarness,
    cookie_header,
    login_instructor,
    new_session,
    wait_for_http,
)


class ExercisesLiveRegressionTests(unittest.TestCase):
    base_url = DEFAULT_BASE_URL

    @classmethod
    def setUpClass(cls) -> None:
        probe = new_session()
        try:
            wait_for_http(
                probe,
                f"{cls.base_url}/instructor/",
                lambda resp: resp.status_code == 200,
                description="shared instructor login page",
            )
            wait_for_http(
                probe,
                f"{cls.base_url}/exercises/bgp/",
                lambda resp: resp.status_code == 200,
                description="bgp exercise home",
            )
            wait_for_http(
                probe,
                f"{cls.base_url}/exercises/insider/",
                lambda resp: resp.status_code == 200,
                description="insider exercise home",
            )
        finally:
            probe.close()

    def test_http_smoke_and_auth_gates(self) -> None:
        # Since the June 2026 pilot the BGP game is student-only (no instructor
        # dashboard); only the Insider game keeps one behind shared auth.
        student = new_session()
        instructor = new_session()
        try:
            login_instructor(instructor, self.base_url)

            bgp = student.get(f"{self.base_url}/exercises/bgp/", timeout=10)
            self.assertEqual(bgp.status_code, 200)
            self.assertIn("Byzantine Generals Simulation", bgp.text)

            bgp_health = student.get(f"{self.base_url}/exercises/bgp/healthz", timeout=10)
            self.assertEqual(bgp_health.status_code, 200)
            self.assertEqual(bgp_health.json()["status"], "ok")

            insider = student.get(f"{self.base_url}/exercises/insider/", timeout=10)
            self.assertEqual(insider.status_code, 200)
            self.assertIn("The Insider", insider.text)

            unauth_insider_instructor = student.get(
                f"{self.base_url}/exercises/insider/instructor",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(unauth_insider_instructor.status_code, (301, 302, 401, 403))

            insider_instructor = instructor.get(
                f"{self.base_url}/exercises/insider/instructor",
                timeout=10,
            )
            self.assertEqual(insider_instructor.status_code, 200)
            self.assertIn("Instructor Dashboard", insider_instructor.text)
        finally:
            instructor.close()
            student.close()

    def test_bgp_solo_room_from_broadcast_to_debrief(self) -> None:
        # One student and three honest bots: every message carries the same
        # order, so the run is deterministic from room creation to debrief.
        student_socket = None
        try:
            student_socket = SocketHarness(
                self.base_url,
                socketio_path="exercises/bgp/socket.io",
                event_names=(
                    "connected",
                    "restore_state",
                    "phase_1_start",
                    "phase_2_start",
                    "room_update",
                    "debrief_ready",
                    "server_error",
                ),
            )
            student_socket.wait_for("connected")
            student_uuid = f"bgp-regression-{uuid_lib.uuid4().hex[:10]}"
            student_socket.emit("register", {"uuid": student_uuid})
            lobby = student_socket.wait_for(
                "restore_state",
                lambda payload: payload and payload.get("view") == "lobby",
            )
            self.assertEqual(lobby["player"]["uuid"], student_uuid)

            student_socket.emit("create_room", {"size": 4, "num_traitors": 0})
            phase_one = student_socket.wait_for("phase_1_start")
            self.assertEqual(phase_one["view"], "broadcast")
            self.assertEqual(phase_one["room"]["size"], 4)
            self.assertEqual(phase_one["room"]["num_traitors"], 0)
            self.assertEqual(phase_one["room"]["total_players"], 4)
            self.assertEqual(len(phase_one["room"]["peer_nodes"]), 3)
            self.assertEqual(phase_one["room"]["broadcast_complete"], 3, "the bots broadcast as soon as the room opens")
            self.assertEqual(phase_one["player"]["role"], "honest")
            order = phase_one["player"]["initial_value"]
            self.assertIn(order, ("Attack", "Retreat"))

            student_socket.emit("submit_broadcast", {"messages": {}})
            phase_two = student_socket.wait_for("phase_2_start")
            self.assertEqual(phase_two["view"], "tally")
            self.assertEqual(len(phase_two["messages"]), 3)
            self.assertEqual({message["value"] for message in phase_two["messages"]}, {order})

            student_socket.emit("submit_final_vote", {"value": order})
            voted = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("view") == "await_debrief",
            )
            self.assertEqual(voted["room"]["vote_complete"], 4)

            student_socket.emit("reveal_room_debrief")
            debrief = student_socket.wait_for("debrief_ready")["debrief"]
            self.assertEqual(debrief["correct_consensus"], order)
            self.assertEqual(len(debrief["edges"]), 12, "each of 4 nodes sends to 3 peers")
            me = next(player for player in debrief["players"] if player["uuid"] == student_uuid)
            self.assertEqual(me["final_vote"], order)
            self.assertTrue(me["survived"])
            self.assertEqual(student_socket.events("server_error"), [])
        finally:
            if student_socket is not None:
                student_socket.disconnect()

    def test_insider_private_room_fills_with_agents_and_instructor_sees_it(self) -> None:
        instructor = new_session()
        student = new_session()
        instructor_socket = None
        student_socket = None
        try:
            login_instructor(instructor, self.base_url)
            instructor_page = instructor.get(
                f"{self.base_url}/exercises/insider/instructor",
                timeout=10,
            )
            self.assertEqual(instructor_page.status_code, 200)

            instructor_socket = SocketHarness(
                self.base_url,
                cookie_header=cookie_header(instructor),
                socketio_path="exercises/insider/socket.io",
                event_names=("instructor_update", "error_message"),
            )
            instructor_socket.emit("instructor_join")
            instructor_socket.wait_for("instructor_update")

            student_socket = SocketHarness(
                self.base_url,
                socketio_path="exercises/insider/socket.io",
                event_names=("joined", "room_update", "role_assigned", "error_message"),
            )
            student_socket.emit("join", {"name": "Regression Student", "join_mode": "create_private"})
            joined = student_socket.wait_for("joined")
            room_id = joined["room_id"]
            self.assertEqual(joined["player_token"], joined["sid"])

            lobby_state = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("room_id") == room_id and payload.get("state") == "lobby",
            )
            self.assertTrue(lobby_state["private_room"])
            self.assertEqual(lobby_state["player_count"], 1)
            self.assertEqual([player["name"] for player in lobby_state["players"]], ["Regression Student"])
            self.assertTrue(lobby_state["settings"]["agents_enabled"])

            qr = student.get(
                f"{self.base_url}/exercises/insider/room/{room_id}/qr.png",
                timeout=10,
            )
            self.assertEqual(qr.status_code, 200)
            self.assertEqual(qr.headers.get("Content-Type"), "image/png")

            instructor_room = instructor_socket.wait_for(
                "instructor_update",
                lambda payload: payload and room_id in (payload.get("rooms") or {}),
            )
            self.assertIn(room_id, instructor_room["rooms"])

            # Below the minimum of 4, agents fill the room up to the recommended 5 when it starts.
            student_socket.emit("start_game")
            role = student_socket.wait_for(
                "role_assigned",
                lambda payload: payload and payload.get("role") in {"insider", "player"},
            )
            if role["role"] == "insider":
                self.assertIsNone(role["word"])
            else:
                self.assertTrue(role["word"])

            clue_state = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("room_id") == room_id and payload.get("state") == "clue",
            )
            self.assertEqual(len(clue_state["players"]), 5)
            self.assertEqual(sum(1 for player in clue_state["players"] if player["is_agent"]), 4)
            self.assertEqual(student_socket.events("error_message"), [])
        finally:
            if instructor_socket is not None:
                instructor_socket.disconnect()
            if student_socket is not None:
                student_socket.disconnect()
            instructor.close()
            student.close()


if __name__ == "__main__":
    unittest.main()
