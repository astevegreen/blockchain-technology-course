"""Runtime secrets: every `${X:?}` a launcher compose file needs gets a value, generated the way
dynamic-labs/runtime-credentials.sh generates it (design section 4, secrets)."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from launcher import secrets_env  # noqa: E402
from fake_docker import Bench  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
LABS = REPO / "dynamic-labs"
REQUIRED = re.compile(r"\$\{([A-Z][A-Z0-9_]*):\?")
# Set by Controller.env(), not secret.
CONTROLLER_VARS = {"COURSE_RELEASE", "HOST_BIND", "HTTP_PORT", "NGINX_CONF", "CLASS_GATE", "LANE_MODE"}


class Coverage(unittest.TestCase):
    def test_every_required_variable_has_a_value(self):
        files = sorted(LABS.rglob("docker-compose.launcher.yml"))
        self.assertTrue(files, "no launcher compose files found")
        missing = {}
        for path in files:
            for name in REQUIRED.findall(path.read_text(encoding="utf-8")):
                covered = name in secrets_env.GENERATORS or name in CONTROLLER_VARS or name.endswith("_IMAGE")
                if not covered:
                    missing.setdefault(name, []).append(path.relative_to(REPO).as_posix())
        self.assertEqual(missing, {}, "add a generator to launcher/secrets_env.py or a value to Controller.env()")

    def test_controller_sets_its_variables(self):
        bench = Bench()
        try:
            self.assertLessEqual(CONTROLLER_VARS, set(bench.controller.env()))
        finally:
            bench.close()

    def test_same_variables_as_runtime_credentials(self):
        text = (LABS / "runtime-credentials.sh").read_text(encoding="utf-8")
        written = re.findall(r"^([A-Z][A-Z0-9_]*)=\$\{\1\}$", text, re.M)
        self.assertEqual(list(secrets_env.GENERATORS), written)


class Ensure(unittest.TestCase):
    def test_generates_once_and_fills_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime-secrets.env"
            first = secrets_env.ensure(path)
            self.assertEqual(set(first), set(secrets_env.GENERATORS))
            self.assertEqual(first["INSTRUCTOR_AUTH_KEY"], first["TRUST_GAME_INSTRUCTOR_PASSWORD"])
            self.assertRegex(first["CLASS_CODE"], r"^[A-HJKMNP-Z2-9]{8}$")
            self.assertEqual(len(first["LANE_SERVICE_SECRET"]), 64)
            text = path.read_text(encoding="utf-8").replace(f"CLASS_CODE={first['CLASS_CODE']}\n", "")
            path.write_text(text, encoding="utf-8")
            second = secrets_env.ensure(path)
            self.assertEqual({k: v for k, v in second.items() if k != "CLASS_CODE"},
                             {k: v for k, v in first.items() if k != "CLASS_CODE"})
            self.assertTrue(second["CLASS_CODE"])


if __name__ == "__main__":
    unittest.main()
