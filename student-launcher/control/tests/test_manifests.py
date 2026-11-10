"""The launcher reads the real lab manifests (dynamic-labs/*/lab.yaml, as S1 committed them) and guards host files."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(REPO / "tools"))

from fake_docker import Bench, lab, router  # noqa: E402
from launcher.release import image_var  # noqa: E402
from launcher.server import dispatch  # noqa: E402

SOCKET = {"type": "bind", "source": "/var/run/docker.sock", "target": "/var/run/docker.sock"}

try:
    import lab_manifest  # noqa: E402 - needs PyYAML, which the check's Python has
except ImportError:  # pragma: no cover
    lab_manifest = None


@unittest.skipIf(lab_manifest is None, "PyYAML isn't installed")
class RealManifests(unittest.TestCase):
    def setUp(self):
        self.manifests = lab_manifest.load_manifests()
        local = [m for m in self.manifests.values() if m.get("student_local")]
        # The release workflow (S5) pushes every build service and records its digest under the image variable.
        images = {image_var(m["id"], name, spec): f"ghcr.io/astevegreen/course-labs@sha256:{i:064x}"
                  for i, (m, name, spec) in enumerate((m, n, sp) for m in local
                                                      for n, sp in m["services"].items() if sp["source"] == "build")}
        self.bench = Bench(labs=local, images=images)

    def tearDown(self):
        self.bench.close()

    def test_every_student_lab_gets_a_row(self):
        c = self.bench.controller
        rows = {row["id"]: row for row in c.labs()}
        expected = {m["id"] for m in self.manifests.values() if m.get("student_local") and m.get("kind") == "lab"}
        self.assertEqual(set(rows), expected)
        for lab_id, row in rows.items():
            self.assertTrue(row["entry_url"].startswith("http://127.0.0.1"), lab_id)
            self.assertGreater(c.needed_mb(c.release.lab(lab_id)), 0, lab_id)
            self.assertTrue(c.release.lab_images(c.release.lab(lab_id)), lab_id)
        self.assertNotIn("router", rows)
        self.assertNotIn("lane-service", rows)

    def test_lane_service_may_bind_the_socket_and_starts(self):
        c = self.bench.controller
        self.assertIs(c.release.lab("lane-service").get("docker_socket"), True)
        self.bench.fake.compose_volumes["lane-service"] = [SOCKET]
        lane_labs = [row["id"] for row in c.labs() if c.release.lab(row["id"]).get("uses_lane_service")]
        self.assertIn("bitcoin", lane_labs)
        status, _ = dispatch(c, "POST", "/api/labs/bitcoin/start")
        self.assertEqual(status, 202)
        self.assertEqual(self.bench.state("bitcoin"), "running")


class HostFiles(unittest.TestCase):
    def tearDown(self):
        self.bench.close()

    def start(self, volumes, **lane):
        self.bench = Bench(labs=[router(), lab("lane-service", kind="shared", **lane),
                                 lab("hlf", uses_lane_service=True)])
        self.bench.fake.compose_volumes["lane-service"] = volumes
        dispatch(self.bench.controller, "POST", "/api/labs/hlf/start")
        return dispatch(self.bench.controller, "GET", "/api/labs")[1]["labs"][0]

    def test_socket_allowed_with_the_flag(self):
        self.assertEqual(self.start([SOCKET], docker_socket=True)["state"], "running")

    def test_socket_refused_without_the_flag(self):
        row = self.start([SOCKET])
        self.assertEqual(row["state"], "error")
        self.assertIn("files on your computer", row["message"])

    def test_other_host_paths_refused_even_with_the_flag(self):
        row = self.start([{"type": "bind", "source": "/home", "target": "/data"}], docker_socket=True)
        self.assertEqual(row["state"], "error")

    def test_named_volumes_are_fine(self):
        self.assertEqual(self.start([{"type": "volume", "source": "data", "target": "/data"}])["state"], "running")


if __name__ == "__main__":
    unittest.main()
