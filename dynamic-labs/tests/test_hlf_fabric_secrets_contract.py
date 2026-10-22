from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HLF = ROOT / "hlf"
RUNTIME_CREDENTIALS = ROOT / "runtime-credentials.sh"
FABRIC_SECRET_NAMES = ("HLF_CA_ADMIN_PASSWORD", "HLF_COUCHDB_PASSWORD")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class FabricSecretsAreNotBuiltInTests(unittest.TestCase):
    """The Fabric CA admin and CouchDB passwords come from the generated env file, never the repo."""

    def test_templates_have_no_built_in_passwords(self) -> None:
        for name in ("compose-ca.yaml.tmpl", "compose-couch.yaml.tmpl"):
            text = read(HLF / "managed_runtime" / name)
            self.assertNotIn("adminpw", text, name)

    def test_templates_fail_closed_when_a_password_is_unset(self) -> None:
        ca = read(HLF / "managed_runtime" / "compose-ca.yaml.tmpl")
        couch = read(HLF / "managed_runtime" / "compose-couch.yaml.tmpl")

        self.assertEqual(3, len(re.findall(r"\$\{HLF_CA_ADMIN_PASSWORD:\?", ca)))
        self.assertEqual(6, len(re.findall(r"\$\{HLF_COUCHDB_PASSWORD:\?", couch)))
        self.assertNotRegex(ca + couch, r"\$\{HLF_[A-Z_]+PASSWORD(:-|\})")

    def test_runner_service_requires_both_passwords(self) -> None:
        compose = read(HLF / "docker-compose.yml")

        for name in FABRIC_SECRET_NAMES:
            self.assertIn(f"{name}: ${{{name}:?", compose)

    def test_lab_script_patches_the_upstream_enrollment_and_stops_if_unpatched(self) -> None:
        lab = read(HLF / "lab.sh")

        # registerEnroll.sh and network.sh are downloaded upstream scripts that enroll as "admin".
        self.assertGreaterEqual(lab.count("-e 's#//admin:adminpw@#//admin:${HLF_CA_ADMIN_PASSWORD}@#g'"), 2)
        self.assertIn("grep -q 'admin:adminpw@' \"${register_enroll}\"", lab)
        self.assertIn("getcainfo -u https://admin:${HLF_CA_ADMIN_PASSWORD}@ca_org1:7054", lab)
        self.assertIn("-e HLF_CA_ADMIN_PASSWORD", lab)

    def test_lab_script_refuses_to_start_without_the_passwords(self) -> None:
        lab = read(HLF / "lab.sh")

        for function in ("start_runtime_ca", "start_runtime_network_containers"):
            body = lab.split(f"{function}() {{", 1)[1].split("\n}\n", 1)[0]
            self.assertIn("require_fabric_secrets", body, function)

    def test_runtime_credentials_generate_and_persist_both(self) -> None:
        script = read(RUNTIME_CREDENTIALS)

        for name in FABRIC_SECRET_NAMES:
            self.assertIn(f"{name}=${{{name}}}", script, "written to the env file")
            self.assertIn(f'{name}="$(runtime_random_alnum 24)"', script, "generated")
            self.assertIn(f'-z "${{{name}:-}}"', script, "backfilled for an older env file")


def _working_python3_dir(scratch: Path) -> str:
    """A directory whose `python3` runs this interpreter, so the script's generator works on any host."""
    shim_dir = scratch / "bin"
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text(f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "$@"\n', encoding="utf-8", newline="\n")
    shim.chmod(0o755)
    return str(shim_dir)


@unittest.skipUnless(shutil.which("bash"), "bash is needed to run runtime-credentials.sh")
class RuntimeCredentialsGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.scratch = Path(self._tmp.name)
        self.labs_root = self.scratch / "labs"
        self.labs_root.mkdir()
        self.env_file = self.labs_root / ".runtime" / "runtime-secrets.env"
        self.path = _working_python3_dir(self.scratch) + os.pathsep + os.environ.get("PATH", "")

    def ensure(self, rotate: str = "0") -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = self.path
        env["DYNAMIC_LABS_ROOT"] = self.labs_root.as_posix()
        subprocess.run(
            ["bash", "-c", f'source "{RUNTIME_CREDENTIALS.as_posix()}"; ensure_runtime_credentials {rotate}'],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return self.read_env()

    def read_env(self) -> dict[str, str]:
        pairs = (line.split("=", 1) for line in read(self.env_file).splitlines() if "=" in line)
        return {key: value for key, value in pairs}

    def test_first_deploy_generates_two_different_alphanumeric_passwords(self) -> None:
        values = self.ensure()

        for name in FABRIC_SECRET_NAMES:
            self.assertRegex(values[name], r"^[A-Za-z0-9]{24}$", name)
        self.assertNotEqual(values["HLF_CA_ADMIN_PASSWORD"], values["HLF_COUCHDB_PASSWORD"])

    def test_plain_redeploy_keeps_them_and_rotation_replaces_them(self) -> None:
        first = self.ensure()
        again = self.ensure()
        rotated = self.ensure(rotate="1")

        for name in FABRIC_SECRET_NAMES:
            self.assertEqual(first[name], again[name], name)
            self.assertNotEqual(first[name], rotated[name], name)

    def test_env_file_from_an_older_release_is_backfilled_without_changing_other_logins(self) -> None:
        first = self.ensure()
        older = "\n".join(
            line for line in read(self.env_file).splitlines() if not line.startswith(("HLF_CA_ADMIN_", "HLF_COUCHDB_"))
        )
        self.env_file.write_text(older + "\n", encoding="utf-8")
        for name in FABRIC_SECRET_NAMES:
            self.assertNotIn(name, self.read_env())

        upgraded = self.ensure()

        for name in FABRIC_SECRET_NAMES:
            self.assertRegex(upgraded[name], r"^[A-Za-z0-9]{24}$", name)
        for name, value in first.items():
            if name not in FABRIC_SECRET_NAMES:
                self.assertEqual(value, upgraded[name], name)


if __name__ == "__main__":
    unittest.main()
