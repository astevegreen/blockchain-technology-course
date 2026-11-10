"""The control container's behaviour against a pretend Docker (fake_docker.py): the API of design section 5,
reconciliation, the classroom refusal, port fallback, memory and processor checks, updates and lab actions."""
from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from fake_docker import GB, Bench, lab, router

from launcher import messages
from launcher.server import dispatch, make_handler


class Api(unittest.TestCase):
    def setUp(self):
        self.bench = Bench()
        self.c = self.bench.controller

    def tearDown(self):
        self.bench.close()

    def call(self, method, path):
        return dispatch(self.c, method, path)

    def test_health_and_unknown_paths(self):
        self.assertEqual(self.call("GET", "/api/health"), (200, {"ok": True, "version": "r1"}))
        self.assertEqual(self.call("GET", "/api/nothing")[0], 404)
        self.assertEqual(self.call("GET", "/api/labs/hello/start")[0], 405)
        self.assertEqual(self.call("POST", "/api/labs/nope/start")[0], 404)

    def test_labs_lists_only_student_labs(self):
        status, body = self.call("GET", "/api/labs")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in body["labs"]], ["hello"])
        self.assertEqual(body["labs"][0]["state"], "not-downloaded")
        self.assertEqual(body["labs"][0]["entry_url"], "http://127.0.0.1/hello/")

    def test_downloaded_when_every_image_is_present(self):
        self.bench.fake.images.add("example/hello:1")
        self.assertEqual(self.bench.state("hello"), "downloaded")

    def test_start_runs_router_then_lab_and_reports_progress(self):
        status, body = self.call("POST", "/api/labs/hello/start")
        self.assertEqual(status, 202)
        self.assertEqual(self.call("GET", "/api/labs/hello/progress")[1]["phase"], "running")
        self.assertEqual(self.bench.state("hello"), "running")
        ups = [c[2] for c in self.bench.fake.calls if c[:1] == ["compose"] and "up" in c]
        self.assertEqual(ups, ["router", "hello"], "the router starts before the lab")
        self.assertTrue(self.bench.fake.ran("network", "create", "router-net"))
        self.assertTrue(self.bench.fake.ran("network", "connect", "--alias", "course-launcher"))
        labels = self.bench.fake.containers[-1]["labels"]
        self.assertEqual((labels["course.lab"], labels["course.release"]), ("hello", "r1"))

    def test_start_writes_every_secret_once(self):
        self.call("POST", "/api/labs/hello/start")
        first = self.c.secrets_file.read_text(encoding="utf-8")
        self.call("POST", "/api/labs/hello/stop")
        self.call("POST", "/api/labs/hello/start")
        self.assertEqual(self.c.secrets_file.read_text(encoding="utf-8"), first, "secrets persist across starts")

    def test_stop_and_reset(self):
        self.call("POST", "/api/labs/hello/start")
        self.assertEqual(self.call("POST", "/api/labs/hello/stop")[0], 200)
        self.assertEqual(self.bench.state("hello"), "stopped")
        self.assertEqual(self.call("POST", "/api/labs/hello/reset")[0], 200)
        self.assertTrue(self.bench.fake.ran("compose", "hello", "down", "-v"))
        self.assertEqual(self.bench.state("hello"), "downloaded")

    def test_docker_not_running_is_plain(self):
        self.bench.fake.info = None
        status, body = self.call("POST", "/api/labs/hello/start")
        self.assertEqual(status, 503)
        self.assertIn("Open Docker Desktop", body["message"])

    def test_failed_start_shows_a_plain_message(self):
        self.bench.fake.fail[("pull",)] = "Error response from daemon: dial tcp: lookup ghcr.io: no such host"
        self.call("POST", "/api/labs/hello/start")
        _, body = self.call("GET", "/api/labs")
        self.assertEqual(body["labs"][0]["state"], "error")
        self.assertEqual(body["labs"][0]["message"], messages.NO_INTERNET)

    def test_offline_with_images_missing(self):
        self.bench.internet = False
        self.call("POST", "/api/labs/hello/start")
        self.assertEqual(self.call("GET", "/api/labs/hello/progress")[1]["message"], messages.NO_INTERNET)

    def test_unexpected_error_never_leaks_a_trace(self):
        self.c.labs = lambda: 1 / 0
        status, body = self.call("GET", "/api/labs")
        self.assertEqual(status, 500)
        self.assertNotIn("ZeroDivision", body["message"])

    def test_shutdown_stops_labs_before_shared_services(self):
        self.call("POST", "/api/labs/hello/start")
        self.assertEqual(self.call("POST", "/api/shutdown")[0], 200)
        stops = [c[2] for c in self.bench.fake.calls if c[:1] == ["compose"] and "stop" in c]
        self.assertEqual(stops, ["hello", "router"])

    def test_system(self):
        self.bench.fake.busy_ports.add(8442)
        body = self.call("GET", "/api/system")[1]
        self.assertEqual((body["docker"]["running"], body["memory_mb"], body["arch"]), (True, 8192, "linux/amd64"))
        self.assertEqual(body["ports"]["8442"], "busy")
        self.assertEqual(body["ports"]["80"], "free")


class Actions(unittest.TestCase):
    def setUp(self):
        self.bench = Bench(labs=[router(), lab("forensics", local_actions=[
            {"id": "seed", "label": "Load the case data", "api": "/api/forensics/seed"}])])

    def tearDown(self):
        self.bench.close()

    def test_action_posts_to_lane_service_only_while_running(self):
        c = self.bench.controller
        self.assertEqual(dispatch(c, "POST", "/api/labs/forensics/actions/seed")[0], 409)
        dispatch(c, "POST", "/api/labs/forensics/start")
        self.assertIsNone(dispatch(c, "GET", "/api/labs")[1]["labs"][0]["action"])
        status, body = dispatch(c, "POST", "/api/labs/forensics/actions/seed")
        self.assertEqual(status, 202, body)
        self.assertEqual(self.bench.posts, ["http://lane-service-lane-service-1:8090/api/forensics/seed"])
        self.assertEqual(dispatch(c, "POST", "/api/labs/forensics/actions/other")[0], 404)
        row = dispatch(c, "GET", "/api/labs")[1]["labs"][0]
        self.assertEqual(row["actions"], [{"id": "seed", "label": "Load the case data"}])
        self.assertEqual((row["action"]["phase"], row["action"]["message"]), ("done", "Done: Load the case data."))
        dispatch(c, "POST", "/api/labs/forensics/stop")
        self.assertIsNone(dispatch(c, "GET", "/api/labs")[1]["labs"][0]["action"])

    def test_the_forensics_button_goes_straight_to_lane_service_not_the_router(self):
        bench = Bench(labs=[router(), lab("bitcoin", local_actions=[
            {"id": "forensics-load", "label": "Load the case data", "api": "/api/local/bitcoin/forensics-load"}])])
        try:
            dispatch(bench.controller, "POST", "/api/labs/bitcoin/start")
            dispatch(bench.controller, "POST", "/api/labs/bitcoin/actions/forensics-load")
            self.assertEqual(bench.posts, ["http://lane-service-lane-service-1:8090/api/local/bitcoin/forensics-load"])
        finally:
            bench.close()

    def test_a_failed_or_slow_button_says_so_plainly_and_runs_once(self):
        c = self.bench.controller
        dispatch(c, "POST", "/api/labs/forensics/start")
        self.bench.post = lambda url, timeout: (0, "timed out")
        c.post = self.bench.post
        dispatch(c, "POST", "/api/labs/forensics/actions/seed")
        row = dispatch(c, "GET", "/api/labs")[1]["labs"][0]
        self.assertEqual(row["action"]["phase"], "error")
        self.assertIn("didn't finish", row["action"]["message"])
        gate = threading.Event()
        calls = []
        c.background = True
        c.post = lambda url, timeout: (calls.append(timeout), gate.wait(5), (200, "{}"))[-1]
        first = dispatch(c, "POST", "/api/labs/forensics/actions/seed")
        again = dispatch(c, "POST", "/api/labs/forensics/actions/seed")
        self.assertEqual((first[1]["phase"], again[1]["phase"]), ("running", "running"))
        gate.set()
        for _ in range(50):
            if c.actions["forensics"].phase != "running":
                break
            time.sleep(0.05)
        self.assertEqual(c.actions["forensics"].phase, "done")
        self.assertEqual(calls, [900])


class Checks(unittest.TestCase):
    def tearDown(self):
        self.bench.close()

    def test_memory_short(self):
        self.bench = Bench()
        self.bench.fake.info["MemTotal"] = GB // 4
        status, body = dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        self.assertEqual(status, 409)
        self.assertIn("raise Memory to at least", body["message"])

    def start_fabric(self, version):
        self.bench = Bench(labs=[router(), lab("hello"), lab("fabric", min_docker_engine="26.0",
                                                               min_docker_desktop="4.29")])
        if version is not None:
            self.bench.fake.info["ServerVersion"] = version
        return dispatch(self.bench.controller, "POST", "/api/labs/fabric/start")

    def test_older_docker_is_refused_with_what_to_update(self):
        status, body = self.start_fabric("25.0.5")
        self.assertEqual(status, 409)
        self.assertEqual(body["message"], "This lab needs Docker Desktop 4.29 or newer. Update Docker Desktop, "
                                          "then press Start again.")
        self.assertFalse(self.bench.fake.ran("compose"))

    def test_other_labs_start_on_older_docker(self):
        self.start_fabric("25.0.5")
        self.assertEqual(dispatch(self.bench.controller, "POST", "/api/labs/hello/start")[0], 202)

    def test_equal_and_newer_docker_start(self):
        for version in ("26.0.0", "26.0", "26.1.3", "27.5.1", "29.0.0-rc.1"):
            self.assertEqual(self.start_fabric(version)[0], 202, version)

    def test_unreadable_docker_version_does_not_block(self):
        for version in (None, "", "unknown"):
            self.assertEqual(self.start_fabric(version)[0], 202, version)

    def test_processor_not_supported(self):
        self.bench = Bench(labs=[router(), lab("amd-only", services={
            "web": {"source": "upstream", "image": "x/y:1", "platforms": ["linux/amd64"]}})])
        self.bench.fake.info["Architecture"] = "aarch64"
        item = dispatch(self.bench.controller, "GET", "/api/labs")[1]["labs"][0]
        self.assertEqual(item["state"], "unavailable")
        self.assertIn("Apple silicon", item["unavailable_reason"])
        self.assertEqual(dispatch(self.bench.controller, "POST", "/api/labs/amd-only/start")[0], 409)

    def test_classroom_stack_refused(self):
        self.bench = Bench()
        self.bench.fake.add_container("hello-web-1", {"com.docker.compose.project": "hello"})
        status, body = dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        self.assertEqual((status, body["message"]), (409, messages.CLASSROOM))

    def test_port_80_busy_falls_back_to_8480(self):
        self.bench = Bench()
        self.bench.fake.busy_ports.add(80)
        dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        self.assertEqual(self.bench.state("hello"), "running")
        item = dispatch(self.bench.controller, "GET", "/api/labs")[1]["labs"][0]
        self.assertEqual(item["entry_url"], "http://127.0.0.1:8480/hello/")

    def test_port_80_fails_late_then_8480(self):
        self.bench = Bench()
        self.bench.fake.fail[("run",)] = "something odd"  # the probe can't tell; compose up finds 80 busy
        self.bench.fake.busy_ports.add(80)
        dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        self.assertEqual(self.bench.controller.http_port(), 8480)

    def test_both_http_ports_busy(self):
        self.bench = Bench()
        self.bench.fake.busy_ports.update({80, 8480})
        dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        message = dispatch(self.bench.controller, "GET", "/api/labs/hello/progress")[1]["message"]
        self.assertIn("80 and 8480", message)

    def test_lab_port_busy_has_no_fallback(self):
        self.bench = Bench()
        self.bench.fake.busy_ports.add(8441)
        dispatch(self.bench.controller, "POST", "/api/labs/hello/start")
        message = dispatch(self.bench.controller, "GET", "/api/labs/hello/progress")[1]["message"]
        self.assertEqual(message, messages.port_busy(8441))

    def test_update_notice(self):
        self.bench = Bench(digest="sha256:new")
        self.assertEqual(dispatch(self.bench.controller, "GET", "/api/update")[1], {"available": True})
        self.bench.digest = "sha256:old"
        self.assertEqual(dispatch(self.bench.controller, "GET", "/api/update")[1], {"available": False})
        self.bench.digest = None  # offline
        self.assertEqual(dispatch(self.bench.controller, "GET", "/api/update")[1], {"available": False})


class ClassroomGuard(unittest.TestCase):
    """Stop, reset, shutdown and reconcile never touch a compose project the classroom stack also uses."""
    CLASS = {"com.docker.compose.project": "hello"}
    OURS = {"com.docker.compose.project": "hello", "course.lab": "hello", "course.release": "r1"}

    def setUp(self):
        self.bench = Bench(labs=[router(), lab("hello"), lab("lanes", uses_lane_service=True)])
        self.c = self.bench.controller
        self.fake = self.bench.fake

    def tearDown(self):
        self.bench.close()

    def touched(self):
        return [c for c in self.fake.calls if c[0] in ("compose", "rm", "stop", "volume")]

    def test_stop_and_reset_refused_when_classroom_containers_share_the_project(self):
        self.fake.add_container("hello-web-1", self.CLASS)
        for verb in ("stop", "reset"):
            status, body = dispatch(self.c, "POST", f"/api/labs/hello/{verb}")
            self.assertEqual((status, body["message"]), (409, messages.CLASSROOM), verb)
        self.assertEqual(self.touched(), [])
        self.assertEqual(len(self.fake.containers), 1)

    def test_mixed_project_is_refused_too(self):
        self.fake.add_container("hello-web-1", self.OURS)
        self.fake.add_container("hello-db-1", self.CLASS)
        self.assertEqual(dispatch(self.c, "POST", "/api/labs/hello/reset")[0], 409)
        self.assertEqual(self.touched(), [])

    def test_lane_lab_reset_refused_before_the_file_less_down(self):
        self.fake.add_container("lanes-lane-1", {"com.docker.compose.project": "lanes"})
        status, body = dispatch(self.c, "POST", "/api/labs/lanes/reset")
        self.assertEqual((status, body["message"]), (409, messages.CLASSROOM))
        self.assertEqual(self.touched(), [])

    def test_labelled_containers_stop_and_reset_as_before(self):
        dispatch(self.c, "POST", "/api/labs/hello/start")
        self.assertEqual(dispatch(self.c, "POST", "/api/labs/hello/stop")[0], 200)
        self.assertTrue(self.fake.ran("compose", "hello", "stop"))
        self.assertEqual(dispatch(self.c, "POST", "/api/labs/hello/reset")[0], 200)
        self.assertTrue(self.fake.ran("compose", "hello", "down", "-v"))

    def test_shutdown_skips_a_project_with_classroom_containers(self):
        dispatch(self.c, "POST", "/api/labs/hello/start")
        self.fake.add_container("hello-extra-1", self.CLASS)
        self.assertEqual(dispatch(self.c, "POST", "/api/shutdown")[0], 200)
        stops = [c[2] for c in self.fake.calls if c[:1] == ["compose"] and "stop" in c]
        self.assertEqual(stops, ["router"])
        self.assertEqual(self.fake.ran("compose", "hello", "stop"), [])

    def test_reconcile_leaves_a_ghost_project_the_classroom_shares(self):
        self.fake.add_container("old-web-1", {"course.lab": "old", "course.release": "r0",
                                              "com.docker.compose.project": "old"})
        self.fake.add_container("old-db-1", {"com.docker.compose.project": "old"})
        self.c.update_state(lambda d: d.setdefault("labs", {}).__setitem__(
            "old", {"images": {}, "compose_project": "old"}))
        self.assertEqual(self.c.reconcile(), {"removed": []})
        self.assertEqual(len(self.fake.containers), 2)
        self.assertEqual(self.touched(), [])


class Reconcile(unittest.TestCase):
    def tearDown(self):
        self.bench.close()

    def test_removed_lab_is_cleaned_up(self):
        self.bench = Bench()
        fake = self.bench.fake
        fake.add_container("old-web-1", {"course.lab": "old", "course.release": "r0",
                                         "com.docker.compose.project": "old"})
        self.bench.controller.update_state(lambda d: d.setdefault("labs", {}).__setitem__(
            "old", {"images": {"OLD_WEB_IMAGE": "example/old:1"}, "compose_project": "old"}))
        self.assertEqual(self.bench.controller.reconcile(), {"removed": ["old"]})
        self.assertFalse([c for c in fake.containers if c["labels"].get("course.lab") == "old"])
        self.assertEqual(fake.removed_images, ["example/old:1"])
        self.assertNotIn("old", self.bench.controller.load_state()["labs"])

    def test_changed_lab_drops_its_volumes(self):
        self.bench = Bench()
        c = self.bench.controller
        dispatch(c, "POST", "/api/labs/hello/start")
        c.update_state(lambda d: d["labs"]["hello"].__setitem__("images", {"HELLO_WEB_IMAGE": "example/hello:0"}))
        dispatch(c, "POST", "/api/labs/hello/stop")
        dispatch(c, "POST", "/api/labs/hello/start")
        self.assertTrue(self.bench.fake.ran("compose", "hello", "down", "-v"))

    def test_changed_lab_keeps_volumes_when_asked(self):
        self.bench = Bench(labs=[router(), lab("hello", keep_volumes_on_update=True)])
        c = self.bench.controller
        dispatch(c, "POST", "/api/labs/hello/start")
        c.update_state(lambda d: d["labs"]["hello"].__setitem__("images", {"HELLO_WEB_IMAGE": "example/hello:0"}))
        dispatch(c, "POST", "/api/labs/hello/start")
        self.assertFalse(self.bench.fake.ran("compose", "hello", "down", "-v"))

    def test_added_lab_appears(self):
        self.bench = Bench(labs=[router(), lab("hello"), lab("new")])
        self.assertEqual({i["id"] for i in dispatch(self.bench.controller, "GET", "/api/labs")[1]["labs"]},
                         {"hello", "new"})


class LaneLabs(unittest.TestCase):
    def setUp(self):
        lane = lab("lane-service", kind="shared", memory_mb=128)
        self.bench = Bench(labs=[router(), lane, lab("hlf", uses_lane_service=True, memory_mb=1024)])

    def tearDown(self):
        self.bench.close()

    def test_lane_lab_runs_through_lane_service(self):
        c = self.bench.controller
        self.assertEqual(c.needed_mb(c.release.lab("hlf")), 1024 + 64 + 128)
        dispatch(c, "POST", "/api/labs/hlf/start")
        self.assertEqual(self.bench.state("hlf"), "running")
        # The lab's default services come up; lanes (a compose profile) are left to lane-service, and its
        # containers are never removed as orphans of the lab's project.
        ups = self.bench.fake.ran("-p", "hlf", "up")
        self.assertEqual(len(ups), 1)
        self.assertNotIn("--profile", ups[0])
        self.assertNotIn("--remove-orphans", ups[0])
        dispatch(c, "POST", "/api/labs/hlf/stop")
        self.assertEqual(self.bench.state("hlf"), "stopped")
        dispatch(c, "POST", "/api/labs/hlf/reset")
        self.assertEqual(self.bench.state("hlf"), "downloaded")

    def test_lane_lab_without_a_compose_file_only_pulls(self):
        c = self.bench.controller
        c.release.compose_file(c.release.lab("hlf")).unlink()
        dispatch(c, "POST", "/api/labs/hlf/start")
        self.assertFalse(self.bench.fake.ran("-p", "hlf", "up"))
        self.assertEqual(self.bench.state("hlf"), "running")


class Http(unittest.TestCase):
    """The real handler: a page on another site can't press the buttons (CSRF)."""

    def setUp(self):
        self.bench = Bench()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.bench.controller))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.bench.close()

    def post(self, path, origin=None):
        headers = {"Origin": origin} if origin else {}
        req = urllib.request.Request(self.base + path, data=b"", method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            with err:
                return err.code, json.loads(err.read())

    def test_other_origin_refused(self):
        self.assertEqual(self.post("/api/labs/hello/stop", "https://evil.example")[0], 403)
        self.assertEqual(self.post("/api/labs/hello/stop", "http://127.0.0.1:8470")[0], 200)

    def test_page_is_served(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as resp:
            self.assertIn(b"<html", resp.read().lower())
        with urllib.request.urlopen(self.base + "/api/health", timeout=10) as resp:
            self.assertEqual(json.loads(resp.read())["ok"], True)


class Messages(unittest.TestCase):
    def test_explain(self):
        self.assertEqual(messages.explain("Bind for 127.0.0.1:8442 failed: port is already allocated", "x"),
                         messages.port_busy(8442))
        self.assertEqual(messages.explain("write /var/lib: no space left on device", "x"), messages.NO_DISK)
        self.assertEqual(messages.explain("pull access denied for ghcr.io/x", "x"), messages.NOT_PUBLISHED)
        self.assertEqual(messages.explain("Enhanced Container Isolation blocks socket mounts", "x"),
                         messages.ISOLATION)
        self.assertEqual(messages.explain("weird", "starting the lab"),
                         messages.GENERIC.format(doing="starting the lab"))
        self.assertEqual(messages.gb(512), "0.5 GB")


if __name__ == "__main__":
    unittest.main()
