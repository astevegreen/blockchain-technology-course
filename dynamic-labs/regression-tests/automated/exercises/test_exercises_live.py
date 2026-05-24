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

            unauth_bgp_instructor = student.get(
                f"{self.base_url}/exercises/bgp/instructor",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(unauth_bgp_instructor.status_code, (301, 302, 401, 403))

            unauth_insider_instructor = student.get(
                f"{self.base_url}/exercises/insider/instructor",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(unauth_insider_instructor.status_code, (301, 302, 401, 403))

            bgp_instructor = instructor.get(f"{self.base_url}/exercises/bgp/instructor", timeout=10)
            self.assertEqual(bgp_instructor.status_code, 200)
            self.assertIn("Byzantine Generals Simulation Control", bgp_instructor.text)

            insider_instructor = instructor.get(
                f"{self.base_url}/exercises/insider/instructor",
                timeout=10,
            )
            self.assertEqual(insider_instructor.status_code, 200)
            self.assertIn("Instructor Dashboard", insider_instructor.text)
        finally:
            instructor.close()
            student.close()

    def test_bgp_socket_self_service_flow(self) -> None:
        instructor = new_session()
        student = new_session()
        instructor_socket = None
        student_socket = None
        try:
            login_instructor(instructor, self.base_url)
            instructor_page = instructor.get(
                f"{self.base_url}/exercises/bgp/instructor",
                timeout=10,
            )
            self.assertEqual(instructor_page.status_code, 200)

            instructor_socket = SocketHarness(
                self.base_url,
                cookie_header=cookie_header(instructor),
                socketio_path="exercises/bgp/socket.io",
                event_names=("connected", "dashboard_state", "self_service_toggled", "server_error"),
            )
            instructor_socket.wait_for("connected")
            instructor_socket.emit("join_instructor")
            instructor_socket.wait_for("dashboard_state")
            instructor_socket.emit("toggle_self_service", {"enabled": True})
            toggled = instructor_socket.wait_for(
                "self_service_toggled",
                lambda payload: bool(payload and payload.get("self_service_enabled")),
            )
            self.assertTrue(toggled["self_service_enabled"])

            student_socket = SocketHarness(
                self.base_url,
                socketio_path="exercises/bgp/socket.io",
                event_names=("connected", "restore_state", "phase_1_start", "server_error"),
            )
            student_socket.wait_for("connected")
            student_uuid = f"bgp-regression-{uuid_lib.uuid4().hex[:10]}"
            student_socket.emit("register", {"uuid": student_uuid, "mode": "single"})
            restore = student_socket.wait_for(
                "restore_state",
                lambda payload: payload and payload.get("view") == "queue",
            )
            self.assertEqual(restore["player"]["uuid"], student_uuid)

            student_socket.emit("create_single_player_room", {"size": 4, "num_traitors": 1})
            phase_one = student_socket.wait_for(
                "phase_1_start",
                lambda payload: payload and payload.get("room", {}).get("session_started") is True,
            )
            self.assertEqual(phase_one["room"]["mode"], "single")
            self.assertEqual(phase_one["room"]["size"], 4)
            self.assertIn(phase_one["view"], ("broadcast", "broadcast_wait"))
        finally:
            if instructor_socket is not None:
                try:
                    instructor_socket.emit("toggle_self_service", {"enabled": False})
                    instructor_socket.wait_for(
                        "self_service_toggled",
                        lambda payload: payload and payload.get("self_service_enabled") is False,
                        timeout_seconds=5,
                    )
                except Exception:
                    pass
                instructor_socket.disconnect()
            if student_socket is not None:
                student_socket.disconnect()
            instructor.close()
            student.close()

    def test_insider_private_room_and_instructor_socket_flow(self) -> None:
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
            student_socket.emit("join", {"name": "Regression Host", "join_mode": "create_private"})
            joined = student_socket.wait_for("joined")
            room_id = joined["room_id"]
            self.assertEqual(joined["player_token"], joined["sid"])

            lobby_state = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("room_id") == room_id and payload.get("state") == "lobby",
            )
            self.assertEqual(lobby_state["host_sid"], joined["sid"])
            self.assertEqual(lobby_state["player_count"], 1)

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

            student_socket.emit("set_fill_with_agents", {"enabled": True})
            fill_enabled = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("room_id") == room_id and payload.get("fill_with_agents") is True,
            )
            self.assertTrue(fill_enabled["fill_with_agents"])

            student_socket.emit("start_game")
            role = student_socket.wait_for(
                "role_assigned",
                lambda payload: payload and payload.get("role") in {"insider", "player"},
            )
            self.assertIn(role["role"], {"insider", "player"})

            clue_state = student_socket.wait_for(
                "room_update",
                lambda payload: payload and payload.get("room_id") == room_id and payload.get("state") == "clue",
            )
            self.assertEqual(clue_state["state"], "clue")
            self.assertGreaterEqual(clue_state["player_count"], 1)
        finally:
            if instructor_socket is not None:
                instructor_socket.disconnect()
            if student_socket is not None:
                student_socket.disconnect()
            instructor.close()
            student.close()


if __name__ == "__main__":
    unittest.main()
