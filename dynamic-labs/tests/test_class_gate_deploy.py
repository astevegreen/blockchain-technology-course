"""The class gate's deploy switch and router wiring.

Option A (owner, 9 Nov 2026): one class code per class, on by default in the
cloud (deploy-cloud.sh), one deploy flag on the classroom server
(lab-manager.sh --class-gate), off on the student VM (--mode student).

The router half is checked as text here and by `nginx -t`/live runs on a
Docker host; tests/test_class_gate.py covers the auth service and
tests/test_lane_service_class_gate.py the lane-service.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router"
LAB_HOSTS = ("explorer-host.conf", "tokens-host.conf", "dex-host.conf", "dex-l2-host.conf")
BASH = shutil.which("bash")


def _bash(script: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BASH, "-c", script],
        cwd=ROOT,
        env={**os.environ, **env},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )


def _location_block(conf: str, header: str) -> str:
    start = conf.index(header)
    depth = 0
    for index in range(conf.index("{", start), len(conf)):
        if conf[index] == "{":
            depth += 1
        elif conf[index] == "}":
            depth -= 1
            if depth == 0:
                return conf[start:index + 1]
    raise AssertionError(f"unclosed block: {header}")


class RouterClassGateContractTests(unittest.TestCase):
    def test_switch_files_and_compose_mount(self) -> None:
        on = (ROUTER / "class-gate/on.conf").read_text(encoding="utf-8")
        off = (ROUTER / "class-gate/off.conf").read_text(encoding="utf-8")
        self.assertIn("auth_request /_auth/class;", on)
        self.assertIn("error_page 403 = @class_login;", on)
        self.assertNotIn("auth_request ", re.sub(r"#.*", "", off))
        compose = (ROUTER / "docker-compose.yml").read_text(encoding="utf-8")
        # Default off: a router started by hand, or on the student VM, is ungated.
        self.assertIn("./class-gate/${CLASS_GATE:-off}.conf:/etc/nginx/class-gate.conf:ro", compose)

    def test_gate_is_included_on_every_student_server(self) -> None:
        routes = (ROUTER / "routes.conf").read_text(encoding="utf-8")
        self.assertIn("include /etc/nginx/routes/_class_gate.conf;", routes)
        self.assertLess(
            routes.index("include /etc/nginx/routes/_auth.conf;"),
            routes.index("include /etc/nginx/routes/_class_gate.conf;"),
        )
        for name in LAB_HOSTS:
            host = (ROUTER / "routes" / name).read_text(encoding="utf-8")
            self.assertIn("include /etc/nginx/routes/_class_gate.conf;", host, name)

    def test_code_page_instructor_pages_and_login_stay_open(self) -> None:
        gate = (ROUTER / "routes/_class_gate.conf").read_text(encoding="utf-8")
        self.assertIn("include /etc/nginx/class-gate.conf;", gate)
        verify = _location_block(gate, "location = /_auth/class")
        self.assertIn("internal;", verify)
        self.assertIn("/api/class/verify", verify)
        self.assertIn("$cookie_class_pass", verify)
        self.assertIn("$cookie_hlf_instructor", verify)
        for header in ("location @class_login", "location = /class ", "location ^~ /class/", "location ^~ /api/class/"):
            self.assertIn("auth_request off;", _location_block(gate, header), header)

        routes = (ROUTER / "routes/_instructor.conf").read_text(encoding="utf-8")
        for header in (
            "location ~ ^/instructor(?<rest>/.*)?$",
            "location ~ ^/api/instructor(?<rest>/.*)?$",
        ):
            self.assertIn("auth_request off;", _location_block(routes, header), header)
        auth = (ROUTER / "routes/_auth.conf").read_text(encoding="utf-8")
        self.assertIn("auth_request off;", _location_block(auth, "location @instructor_login"))

    def test_class_and_instructor_checks_cache_in_separate_zones(self) -> None:
        # A shared zone would let a crafted hlf_instructor cookie equal to a
        # class-pass cache key replay a class pass as an instructor pass.
        gate = _location_block((ROUTER / "routes/_class_gate.conf").read_text(encoding="utf-8"),
                               "location = /_auth/class")
        auth = _location_block((ROUTER / "routes/_auth.conf").read_text(encoding="utf-8"),
                               "location = /_auth/instructor")
        zone = re.compile(r"^\s*proxy_cache\s+(\S+);", re.MULTILINE)
        self.assertEqual(zone.findall(gate), ["class_pass_cache"])
        self.assertEqual(zone.findall(auth), ["instructor_auth_cache"])
        cache = (ROUTER / "nginx-cache.conf").read_text(encoding="utf-8")
        self.assertIn("keys_zone=class_pass_cache:", cache)
        self.assertIn("keys_zone=instructor_auth_cache:", cache)

    def test_ethereum_sends_only_a_refused_resolve_to_the_code_page(self) -> None:
        conf = (ROUTER / "routes/ethereum.conf").read_text(encoding="utf-8")
        claims = conf.count("error_page 401 = @ethereum_claim;")
        self.assertGreater(claims, 0)
        self.assertEqual(conf.count("error_page 403 = @ethereum_forbidden;"), claims)
        self.assertNotIn("error_page 403 = @class_login;", conf)
        # The lab's own 403 must stay a 403 (proxy_intercept_errors is on there):
        # only a refused resolve subrequest, with no lane host, goes to the code page.
        forbidden = _location_block(conf, "location @ethereum_forbidden")
        self.assertIn('if ($resolved_host != "") {', forbidden)
        self.assertIn("return 403;", forbidden)
        self.assertIn("auth_request off;", forbidden)  # else the server-level gate refuses it again
        self.assertIn("/api/class/return-to", forbidden)

    def test_services_read_the_switch(self) -> None:
        auth = (ROOT / "instructor_auth_service/docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("CLASS_GATE=${CLASS_GATE:-off}", auth)
        self.assertIn("CLASS_CODE=${CLASS_CODE:-}", auth)
        lanes = (ROOT / "lane-service/docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("CLASS_GATE=${CLASS_GATE:-off}", lanes)
        creds = (ROOT / "runtime-credentials.sh").read_text(encoding="utf-8")
        self.assertIn('CLASS_CODE="$(runtime_class_code)"', creds)


@unittest.skipUnless(BASH, "bash is not on PATH")
class DeploySwitchTests(unittest.TestCase):
    def test_deploy_cloud_turns_the_gate_on_by_default(self) -> None:
        result = _bash(
            "bash deploy-cloud.sh --domain lab.example.org --max-student-capacity 30",
            DEPLOY_CLOUD_PRINT_LAB_MANAGER_ARGS_ONLY="1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["deploy", "--mode", "instructor", "--class-gate",
                                                 "--max-student-capacity", "30"])

    def test_deploy_cloud_can_leave_the_gate_off(self) -> None:
        result = _bash(
            "bash deploy-cloud.sh --domain lab.example.org --no-class-gate",
            DEPLOY_CLOUD_PRINT_LAB_MANAGER_ARGS_ONLY="1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["deploy", "--mode", "instructor"])

    def _parse(self, args: str) -> subprocess.CompletedProcess[str]:
        return _bash(
            "source ./lab-manager.sh\n"
            "reset_defaults\n"
            f"parse_deploy_args {args}\n"
            'echo "CLASS_GATE=${CLASS_GATE} EFFECTIVE=$(effective_class_gate)"\n'
        )

    def test_classroom_server_turns_it_on_with_one_flag(self) -> None:
        on = self._parse("--mode instructor --class-gate")
        self.assertEqual(on.returncode, 0, on.stdout + on.stderr)
        self.assertIn("CLASS_GATE=on EFFECTIVE=on", on.stdout)
        off = self._parse("--mode instructor")
        self.assertEqual(off.returncode, 0, off.stdout + off.stderr)
        self.assertIn("CLASS_GATE=off EFFECTIVE=off", off.stdout)

    def test_student_vm_refuses_the_gate(self) -> None:
        refused = self._parse("--mode student --class-gate")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--class-gate is only valid in instructor mode", refused.stdout)
        plain = self._parse("--mode student")
        self.assertEqual(plain.returncode, 0, plain.stdout + plain.stderr)
        self.assertIn("EFFECTIVE=off", plain.stdout)

    def test_saved_state_from_student_mode_never_gates(self) -> None:
        # A hand-edited .lab-manager.env cannot gate the student VM.
        result = _bash(
            "source ./lab-manager.sh\n"
            "reset_defaults\n"
            "MODE=student CLASS_GATE=on\n"
            "effective_class_gate\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "off")

    def test_cloud_host_puts_the_pass_on_the_course_domain(self) -> None:
        result = _bash(
            "source ./lab-manager.sh\n"
            "reset_defaults\n"
            "MODE=instructor CLASS_GATE=on\n"
            'tmp="$(mktemp -d)"\n'
            'printf "lab.example.org\\n" > "${tmp}/cloud-domain.txt"\n'
            'RUNTIME_DIR="${tmp}"\n'
            "unset CLASS_PASS_COOKIE_DOMAIN\n"
            "export_class_gate\n"
            'rm -rf "${tmp}"\n'
            'echo "${CLASS_GATE} ${CLASS_PASS_COOKIE_DOMAIN}"\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "on lab.example.org")

    def test_gate_choice_is_saved_for_later_starts(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")
        self.assertIn("printf 'CLASS_GATE=%q\\n' \"${CLASS_GATE}\"", script)
        self.assertEqual(script.count("export_class_gate\n"), 3)  # compose_up_cmd and both router starts


if __name__ == "__main__":
    unittest.main()
