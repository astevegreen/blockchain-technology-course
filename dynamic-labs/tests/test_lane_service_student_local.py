"""lane-service in LANE_MODE=student-local, the course launcher on a student's own machine.

docs/student-launcher-design.md section 2 item 5: one lane per lab, no class code or claim screen, no host home
folders. Classroom mode must not change, so each setting is also checked with LANE_MODE unset. The launcher compose files are checked for the launcher's rules:
images only, no host folders, and image variables named <ID>_<SERVICE>_IMAGE.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
LANE_SERVICE = ROOT / "lane-service"

# Prints what each lab module settles at import, plus the bitcoin routes Flask registers. Module-level settings
# are read once at import, so each mode runs in its own process.
_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from flask import Flask
import labs.bitcoin as b, labs.consensus as c
app = Flask("probe")
app.register_blueprint(b.blueprint)
out = {
    "routes": sorted(r.rule for r in app.url_map.iter_rules()),
    "labs": {
        m.__name__: {"count": m.STUDENT_COUNT, "warm": m.DEFAULT_WARM_POOL_SIZE, "home": m.STUDENT_HOME_ROOT,
                     "local": m.config.student_local, "config_count": m.config.student_count}
        for m in (b, c)
    },
}
print("PROBE" + json.dumps(out))
"""

def _run_probe(script: str, extra_env: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: v for k, v in os.environ.items() if k != "LANE_MODE"}
        for lab in ("BITCOIN", "CONSENSUS"):
            env[f"{lab}_STATE_DIR"] = str(Path(tmp) / lab.lower())
        env.update(extra_env)
        result = subprocess.run(
            [sys.executable, "-c", script, str(LANE_SERVICE)],
            capture_output=True, text=True, env=env, cwd=tmp, timeout=120,
        )
    line = next((ln for ln in result.stdout.splitlines() if ln.startswith("PROBE")), None)
    if line is None:
        raise AssertionError(f"probe failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(line[len("PROBE"):])


class LabSettingsTests(unittest.TestCase):
    """What each lane lab module settles at import time, in each mode."""

    @classmethod
    def setUpClass(cls) -> None:
        home = tempfile.gettempdir()
        base = {
            "MAX_STUDENT_CAPACITY": "7", "STUDENT_WARM_POOL_SIZE": "2",
            "BITCOIN_STUDENT_HOME_ROOT": home, "CONSENSUS_STUDENT_HOME_ROOT": home,
        }
        cls.home = home
        cls.classroom = _run_probe(_PROBE, base)
        cls.local = _run_probe(_PROBE, {**base, "LANE_MODE": "student-local"})

    def test_student_local_runs_one_lane_with_no_warm_pool_or_host_home(self) -> None:
        for name, lab in self.local["labs"].items():
            with self.subTest(lab=name):
                self.assertEqual(lab["count"], 1)
                self.assertEqual(lab["config_count"], 1)
                self.assertEqual(lab["warm"], 0)
                self.assertIsNone(lab["home"])
                self.assertTrue(lab["local"])

    def test_classroom_settings_are_unchanged(self) -> None:
        labs = self.classroom["labs"]
        for name, lab in labs.items():
            with self.subTest(lab=name):
                self.assertEqual(lab["count"], 7)
                self.assertEqual(lab["config_count"], 7)
                self.assertEqual(lab["warm"], 2)
                self.assertFalse(lab["local"])
        self.assertEqual(labs["labs.bitcoin"]["home"], self.home)
        self.assertEqual(labs["labs.consensus"]["home"], self.home)

    def test_no_forensics_route_in_either_mode(self) -> None:
        # Bitcoin Forensics 1 to 3 were archived at step 7 of the lab plan (archive/dynamic-labs/README.md).
        for mode, out in (("local", self.local), ("classroom", self.classroom)):
            with self.subTest(mode=mode):
                self.assertEqual([r for r in out["routes"] if "forensics" in r], [])


def _lane_modules():
    if str(LANE_SERVICE) not in sys.path:
        sys.path.insert(0, str(LANE_SERVICE))
    import generic_claims
    import generic_lanes
    return generic_lanes, generic_claims


class _FakeLanes:
    def __init__(self) -> None:
        self.stopped: list[str] = []

    def list_lanes(self):
        return [{"id": f"s{n:02d}", "status": "stopped"} for n in range(1, 4)]

    def start_lane(self, lane_id: str):
        return True, "started"

    def stop_lane(self, lane_id: str, *args, **kwargs):
        self.stopped.append(lane_id)
        return True, "stopped"

    def __getattr__(self, name):  # anything else the claim manager asks of the lanes is a no-op
        return lambda *args, **kwargs: None


class ClaimTests(unittest.TestCase):
    def _manager(self, tmp: str, local: bool):
        generic_lanes, generic_claims = _lane_modules()
        env = {k: v for k, v in os.environ.items() if k != "LANE_MODE"}
        if local:
            env["LANE_MODE"] = "student-local"
        with patch.dict(os.environ, env, clear=True):
            config = generic_lanes.LaneConfig(
                lab_name="probe", container_name_fn=lambda lid: f"probe-{lid}", state_dir=Path(tmp),
                student_count=3, idle_timeout=1, student_home_root=tmp,
            )
        lanes = _FakeLanes()
        return config, generic_claims.ClaimManager(config, lanes), lanes

    def test_config_forces_one_lane_and_no_host_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config, _, _ = self._manager(tmp, local=True)
            self.assertTrue(config.student_local)
            self.assertEqual(config.student_count, 1)
            self.assertIsNone(config.student_home_root)
        with tempfile.TemporaryDirectory() as tmp:
            classroom, _, _ = self._manager(tmp, local=False)
            self.assertFalse(classroom.student_local)
            self.assertEqual(classroom.student_count, 3)
            self.assertEqual(classroom.student_home_root, tmp)

    def test_a_new_browser_gets_the_same_lane_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, claims, _ = self._manager(tmp, local=True)
            first, station, _ = claims.claim(None)
            self.assertEqual(station, "s01")
            self.assertEqual(claims.claim(None), (first, "s01", "resumed"))
            self.assertEqual(claims.claim("00000000-0000-4000-8000-000000000000"), (first, "s01", "resumed"))

    def test_classroom_gives_each_new_browser_its_own_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, claims, _ = self._manager(tmp, local=False)
            first, s1, _ = claims.claim(None)
            second, s2, _ = claims.claim(None)
            self.assertNotEqual(first, second)
            self.assertNotEqual(s1, s2)

    def test_the_sweeper_never_releases_the_local_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, claims, lanes = self._manager(tmp, local=True)
            uuid, _, _ = claims.claim(None)
            for entry in claims._claims.values():
                entry["last_active"] = 0
            self.assertEqual(claims._sweep_once(), [])
            self.assertEqual(lanes.stopped, [])
            self.assertEqual(claims.resolve(uuid), "s01")

    def test_lane_containers_carry_launcher_labels_only_locally(self) -> None:
        generic_lanes, _ = _lane_modules()
        env = {k: v for k, v in os.environ.items() if k != "LANE_MODE"}
        env["COURSE_RELEASE"] = "2026.11.09-1"
        with patch.dict(os.environ, {**env, "LANE_MODE": "student-local"}, clear=True):
            self.assertEqual(
                generic_lanes.student_local_labels("consensus"),
                ["--label", "course.lab=consensus", "--label", "course.release=2026.11.09-1"],
            )
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(generic_lanes.student_local_labels("consensus"), [])

    def _docker_run_args(self, tmp: str, env: dict, course_lab):
        """The `docker run` arguments LaneManager sends when it starts a new lane container (Docker faked)."""
        generic_lanes, _ = _lane_modules()
        with patch.dict(os.environ, env, clear=True):
            config = generic_lanes.LaneConfig(
                lab_name="consensus-probe", container_name_fn=lambda lid: f"probe-{lid}", state_dir=Path(tmp),
                student_count=1, image="probe-image", network="probe-net", course_lab=course_lab,
            )
            manager = generic_lanes.LaneManager(config)
            calls: list[list[str]] = []
            ok = SimpleNamespace(returncode=0, stdout="", stderr="")
            with patch.object(manager, "_container_exists_direct", return_value=False), \
                    patch.object(manager, "_run", side_effect=lambda cmd, timeout=120: calls.append(cmd) or ok):
                self.assertEqual(manager._start_docker_run("s01"), (True, "started"))
        runs = [c for c in calls if c[:2] == ["docker", "run"]]
        self.assertEqual(len(runs), 1)
        return runs[0]

    def test_docker_run_of_a_lane_carries_the_launcher_labels(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("LANE_MODE", "COURSE_RELEASE")}
        local = {**env, "LANE_MODE": "student-local", "COURSE_RELEASE": "2026.11.09-1"}
        with tempfile.TemporaryDirectory() as tmp:
            cmd = self._docker_run_args(tmp, local, "consensus")
            labels = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "--label"]
            self.assertEqual(labels, ["course.lab=consensus", "course.release=2026.11.09-1"])
            self.assertLess(cmd.index("--label"), cmd.index("probe-image"))  # flags come before the image
        with tempfile.TemporaryDirectory() as tmp:  # no lab id given: the lab name stands in
            cmd = self._docker_run_args(tmp, local, None)
            self.assertIn("course.lab=consensus-probe", cmd)
        with tempfile.TemporaryDirectory() as tmp:  # classroom: no labels at all
            cmd = self._docker_run_args(tmp, env, "consensus")
            self.assertNotIn("--label", cmd)


LAUNCHER_FILES = {  # lab id: launcher compose file
    "lane-service": "lane-service/docker-compose.launcher.yml",
    "bitcoin": "bitcoin/docker-compose.launcher.yml",
    "consensus": "consensus/docker-compose.launcher.yml",
    "cryptography": "cryptography/docker-compose.launcher.yml",
}
# The one host path a launcher file may name: lane-service starts lanes through the Docker socket.
ALLOWED_BINDS = {("lane-service", "/var/run/docker.sock")}


def _image_var(lab_id: str, service: str) -> str:
    return f"{lab_id}_{service}_IMAGE".upper().replace("-", "_")


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


class LauncherComposeTests(unittest.TestCase):
    def test_launcher_files_use_images_only_and_no_host_folders(self) -> None:
        for lab_id, rel in LAUNCHER_FILES.items():
            for name, svc in _load(rel)["services"].items():
                with self.subTest(file=rel, service=name):
                    self.assertNotIn("build", svc)
                    self.assertNotIn("ports", svc)
                    self.assertEqual(svc["image"], "${%s:?}" % _image_var(lab_id, name))
                    for vol in svc.get("volumes", []):
                        if isinstance(vol, dict):
                            if vol.get("type") == "bind":
                                self.assertIn((lab_id, vol["source"]), ALLOWED_BINDS)
                            continue
                        self.assertFalse(vol.split(":", 1)[0].startswith((".", "/", "~", "$")), vol)

    def test_launcher_files_keep_classroom_project_service_and_container_names(self) -> None:
        for lab_id, rel in LAUNCHER_FILES.items():
            launcher = _load(rel)
            classroom = _load(rel.replace(".launcher", ""))
            folder = Path(rel).parent.name
            with self.subTest(file=rel):
                self.assertEqual(launcher.get("name", folder), classroom.get("name", folder))
                self.assertLessEqual(set(launcher["services"]), set(classroom["services"]))
                for name, svc in launcher["services"].items():
                    self.assertEqual(svc.get("container_name"), classroom["services"][name].get("container_name"))
                    self.assertEqual(svc["labels"]["course.lab"], lab_id)
                    self.assertEqual(svc["labels"]["course.release"], "${COURSE_RELEASE:?}")

    def test_lane_service_gets_every_lane_image_its_labs_pull(self) -> None:
        env = _load(LAUNCHER_FILES["lane-service"])["services"]["lane-service"]["environment"]
        values = dict(item.split("=", 1) for item in env)
        self.assertEqual(values["LANE_MODE"], "student-local")
        self.assertEqual(values["BITCOIN_IMAGE"], "${BITCOIN_STUDENT_IMAGE:?}")
        self.assertEqual(values["CONSENSUS_IMAGE"], "${CONSENSUS_STUDENT_IMAGE:?}")
        # lane-service's own `docker compose up` on the baked bitcoin file must interpolate every variable it uses.
        bitcoin = (ROOT / LAUNCHER_FILES["bitcoin"]).read_text(encoding="utf-8")
        for var in set(re.findall(r"\$\{([A-Z0-9_]+)[:}]", bitcoin)):
            self.assertIn(var, values, var)

    def test_lane_images_are_pulled_but_not_started_by_compose(self) -> None:
        for lab_id in ("bitcoin", "consensus"):
            student = _load(LAUNCHER_FILES[lab_id])["services"]["student"]
            self.assertEqual(student.get("profiles"), ["lane-image"], lab_id)

    def test_launcher_image_bakes_what_lane_service_reads_and_no_answers(self) -> None:
        dockerfile = (LANE_SERVICE / "Dockerfile.launcher").read_text(encoding="utf-8")
        self.assertIn("COPY bitcoin/docker-compose.launcher.yml /app/bitcoin-compose/", dockerfile)
        self.assertIn("LANE_MODE=student-local", dockerfile)
        copies = [ln for ln in dockerfile.splitlines() if ln.startswith("COPY") or ln.startswith("     ")]
        for answer in ("lab.md", "solution.md", "cryptography/"):
            self.assertFalse(any(answer in ln for ln in copies), answer)


class LauncherBakeTests(unittest.TestCase):
    def _bake(self):
        if str(LANE_SERVICE) not in sys.path:
            sys.path.insert(0, str(LANE_SERVICE))
        import launcher_bake
        return launcher_bake

    def test_solutions_are_removed_from_the_catalog(self) -> None:
        bake = self._bake()
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "catalog.yaml"
            catalog.write_text("exercises:\n- id: a\n  solution: x\n- id: b\n  steps: [one]\n", encoding="utf-8")
            self.assertEqual(bake.main(str(catalog)), 0)
            data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
            self.assertEqual([ex["id"] for ex in data["exercises"]], ["a", "b"])
            self.assertNotIn("solution", catalog.read_text(encoding="utf-8"))

    def test_the_shipped_catalog_has_no_solutions(self) -> None:
        data = yaml.safe_load((LANE_SERVICE / "labs/bitcoin_catalog.yaml").read_text(encoding="utf-8"))
        self.assertEqual(self._bake().strip_solutions(data), 0)


if __name__ == "__main__":
    unittest.main()
