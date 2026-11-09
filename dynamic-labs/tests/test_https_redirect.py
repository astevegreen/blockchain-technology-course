"""Plain port 80 redirects to HTTPS on a cloud host (docs/follow-ups.md, 9 Nov 2026 class gate review).

nginx-ssl.conf serves every host on ports 80 and 443. On a cloud host with a domain
(deploy-cloud.sh, which starts the router with docker-compose.cloud.yml), a class code
or instructor login sent to http:// would travel unencrypted, so the cloud overlay
mounts https-redirect/on.conf: port 80 answers with a 301 to the same host and path
over HTTPS. The classroom server and the student VM (by IP address, self-signed
certificate) keep off.conf. The Let's Encrypt certificate needs nothing on port 80
from the router: deploy-cloud.sh runs certbot --standalone before the router starts.

Checked as text here; tests/test_class_gate_deploy.py covers the class gate's switch.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router"
INCLUDE = "include /etc/nginx/https-redirect.conf;"
TARGET = "/etc/nginx/https-redirect.conf"
DOCKER = shutil.which("docker")


def _code(text: str) -> str:
    return re.sub(r"#.*", "", text)


def _servers(conf: str) -> list[str]:
    """Each top-level `server { ... }` block of an nginx config."""
    blocks, start, depth = [], None, 0
    text = _code(conf)
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = text.rindex("server", 0, index)
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                blocks.append(text[start:index + 1])
    return blocks


class HttpsRedirectTests(unittest.TestCase):
    def test_on_redirects_plain_http_with_301_to_same_host_and_path(self) -> None:
        on = _code((ROUTER / "https-redirect/on.conf").read_text(encoding="utf-8"))
        self.assertRegex(on, r"if \(\$scheme = http\) \{\s*return 301 https://\$host\$request_uri;\s*\}")

    def test_off_does_nothing(self) -> None:
        off = _code((ROUTER / "https-redirect/off.conf").read_text(encoding="utf-8"))
        self.assertEqual(off.strip(), "")

    def test_every_tls_server_that_listens_on_80_includes_the_switch(self) -> None:
        servers = _servers((ROUTER / "nginx-ssl.conf").read_text(encoding="utf-8"))
        self.assertEqual(len(servers), 5)  # the default server and explorer, tokens, dex, dex-l2
        for server in servers:
            self.assertRegex(server, r"listen 80;")
            self.assertIn(INCLUDE, server, server[:80])
            # Server level, so the redirect comes before any location, class gate or login.
            self.assertLess(server.index(INCLUDE), server.index("include /etc/nginx/route"), server[:80])

    def test_plain_http_config_never_redirects(self) -> None:
        # nginx-http.conf (--no-tls) has no port 443: a redirect there would loop.
        self.assertNotIn("https-redirect", (ROUTER / "nginx-http.conf").read_text(encoding="utf-8"))

    def test_off_by_default_and_on_in_the_cloud_overlay(self) -> None:
        base = (ROUTER / "docker-compose.yml").read_text(encoding="utf-8")
        cloud = (ROUTER / "docker-compose.cloud.yml").read_text(encoding="utf-8")
        self.assertIn(f"./https-redirect/off.conf:{TARGET}:ro", base)
        self.assertNotIn("https-redirect/on.conf", base)
        self.assertIn(f"./https-redirect/on.conf:{TARGET}:ro", cloud)

    def test_cloud_router_starts_with_the_overlay(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")
        self.assertIn("-f docker-compose.yml -f docker-compose.cloud.yml up -d", script)

    @unittest.skipUnless(DOCKER, "docker is not on PATH")
    def test_compose_merges_on_over_off(self) -> None:
        # Compose merges volumes by container path, so the overlay's on.conf replaces off.conf.
        def mounted(*files: str) -> list[str]:
            args = [DOCKER, "compose"]
            for name in files:
                args += ["-f", name]
            result = subprocess.run(args + ["config", "--format", "json"], cwd=ROUTER, capture_output=True,
                                    text=True, timeout=60)
            if result.returncode != 0:
                self.skipTest(f"docker compose config failed: {result.stderr.strip()[:200]}")
            volumes = json.loads(result.stdout)["services"]["router"]["volumes"]
            return [Path(v["source"]).name for v in volumes if v["target"] == TARGET]

        self.assertEqual(mounted("docker-compose.yml"), ["off.conf"])
        self.assertEqual(mounted("docker-compose.yml", "docker-compose.cloud.yml"), ["on.conf"])


if __name__ == "__main__":
    unittest.main()
