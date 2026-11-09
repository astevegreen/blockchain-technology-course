from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The router is the class's only door: its ports follow HOST_BIND (router/docker-compose.yml). Every other
# container a deploy starts may publish a host port for local debugging, but only on 127.0.0.1. A port on the
# host's public address skips the router's instructor gate, and on a cloud host Docker's published ports go
# around a host firewall such as ufw (docs/security-triage.md, C9: the Ethereum instructor container's 5173
# served an unauthenticated shell that way until 9 Nov 2026).
EXEMPT = {"router/docker-compose.yml", "router/docker-compose.cloud.yml"}

# The ethereum_lab's other compose files are standalone and laptop variants that lab-manager.sh never starts.
NOT_DEPLOYED = {
    "ethereum_lab/docker-compose.fullstack-local.yml",
    "ethereum_lab/docker-compose.instructor-minimal.yml",
    "ethereum_lab/docker-compose.student.yml",
}

LOOPBACK = re.compile(r'^"?(127\.0\.0\.1|\$\{[A-Z0-9_]+:-127\.0\.0\.1\}):')


def deployed_compose_files() -> list[Path]:
    files = sorted(ROOT.glob("*/docker-compose*.yml")) + sorted(ROOT.glob("*/compose.yaml"))
    files += sorted((ROOT / "hlf" / "managed_runtime").glob("compose-*.yaml*"))
    return [
        path for path in files
        if path.relative_to(ROOT).as_posix() not in EXEMPT | NOT_DEPLOYED
    ]


def port_entries(text: str) -> list[str]:
    """The items of every `ports:` list in a compose file, as written."""
    entries = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)ports:\s*$", line)
        if not match:
            continue
        indent = len(match.group(1))
        for item in lines[index + 1:]:
            if not item.strip() or item.lstrip().startswith("#"):
                continue
            if len(item) - len(item.lstrip()) < indent or not item.lstrip().startswith("-"):
                break
            entries.append(item.strip()[1:].split("#", 1)[0].strip())
    return entries


class HostPortsListenOnLoopbackTests(unittest.TestCase):
    def test_the_files_are_found(self) -> None:
        names = {path.relative_to(ROOT).as_posix() for path in deployed_compose_files()}
        for expected in (
            "ethereum_lab/docker-compose.yml",
            "hlf/docker-compose.yml",
            "hlf/managed_runtime/compose-test-net.yaml.tmpl",
            "quiz-engine-v2/compose.yaml",
        ):
            self.assertIn(expected, names)

    def test_every_published_port_is_bound_to_loopback(self) -> None:
        for path in deployed_compose_files():
            for entry in port_entries(path.read_text(encoding="utf-8")):
                with self.subTest(file=path.relative_to(ROOT).as_posix(), port=entry):
                    self.assertRegex(entry, LOOPBACK)

    def test_the_parser_sees_a_public_port(self) -> None:
        sample = "services:\n  a:\n    ports:\n      - \"5173:5173\"\n      - 127.0.0.1:8545:8545\n    env: x\n"
        self.assertEqual(port_entries(sample), ['"5173:5173"', "127.0.0.1:8545:8545"])
        self.assertNotRegex(port_entries(sample)[0], LOOPBACK)


if __name__ == "__main__":
    unittest.main()
