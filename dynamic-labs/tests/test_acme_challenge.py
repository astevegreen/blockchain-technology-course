"""The cloud router serves Let's Encrypt's challenge path on port 80 (docs/follow-ups.md, 9 Nov 2026 HTTPS redirect).

The Let's Encrypt certificate lasts 90 days. deploy-cloud.sh gets it with certbot --webroot, so certbot's
renewal timer renews it the same way while the labs are up: certbot writes a token into
/var/www/course-labs-acme, the cloud router mounts that folder (docker-compose.cloud.yml) and
https-redirect/on.conf serves /.well-known/acme-challenge/ from it over plain HTTP, past the redirect and
the class gate. scripts/cloud-cert-deploy-hook.sh then copies the new certificate to the router and
reloads it.

The live test runs the real router config (nginx-ssl.conf with the cloud switches: redirect on, class gate
on) in nginx:alpine on a Docker host and asks it over HTTP. A real Let's Encrypt renewal needs the real
cloud host (docs/follow-ups.md, "Lab hosting is decided").
"""

from __future__ import annotations

import http.client
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router"
HOOK = ROOT / "scripts" / "cloud-cert-deploy-hook.sh"
DOCKER = shutil.which("docker")
BASH = shutil.which("bash")
IMAGE = "nginx:alpine"
WEBROOT = "/var/www/course-labs-acme"
CERTS = "/etc/course-labs/router-certs"


def _docker(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run([DOCKER, *args], capture_output=True, text=True, timeout=timeout)


class AcmeWiringTests(unittest.TestCase):
    """The folders deploy-cloud.sh, the hook and the cloud overlay share."""

    def test_overlay_mounts_the_webroot_and_the_copied_certificate(self) -> None:
        cloud = re.sub(r"#.*", "", (ROUTER / "docker-compose.cloud.yml").read_text(encoding="utf-8"))
        self.assertIn(f"{WEBROOT}:/var/www/acme:ro", cloud)
        self.assertIn(f"{CERTS}:/etc/nginx/certs:ro", cloud)
        # The live/ symlinks pin the old files under a file mount; the overlay no longer uses them.
        self.assertNotIn("/etc/letsencrypt/live", cloud)

    def test_on_conf_serves_the_webroot_without_the_class_gate(self) -> None:
        on = (ROUTER / "https-redirect/on.conf").read_text(encoding="utf-8")
        self.assertIn("location ^~ /.well-known/acme-challenge/", on)
        self.assertIn("root /var/www/acme;", on)
        self.assertIn("auth_request off;", on)

    def test_deploy_cloud_issues_through_the_webroot_and_installs_renewal(self) -> None:
        script = (ROOT / "deploy-cloud.sh").read_text(encoding="utf-8")
        self.assertIn(f'ACME_WEBROOT="{WEBROOT}"', script)
        self.assertIn('certbot certonly --webroot -w "$ACME_WEBROOT"', script)
        self.assertNotIn("--standalone --cert-name", script)
        self.assertIn("/etc/letsencrypt/renewal-hooks/deploy/", script)
        self.assertIn("certbot.timer", script)
        self.assertIn('scripts/cloud-cert-deploy-hook.sh" "$DOMAIN"', script)
        hook = HOOK.read_text(encoding="utf-8")
        self.assertIn(f'ROUTER_CERT_DIR="${{ROUTER_CERT_DIR:-{CERTS}}}"', hook)

    def test_classroom_and_vm_configs_have_no_challenge_path(self) -> None:
        for name in ("https-redirect/off.conf", "nginx-http.conf", "docker-compose.yml"):
            self.assertNotIn("acme", (ROUTER / name).read_text(encoding="utf-8"), name)


@unittest.skipUnless(BASH, "bash is not on PATH")
class DeployHookTests(unittest.TestCase):
    def _run(self, lineage: str | None) -> tuple[subprocess.CompletedProcess[str], Path]:
        tmp = Path(tempfile.mkdtemp(prefix="cert-hook."))
        self.addCleanup(shutil.rmtree, tmp, True)
        live = tmp / "le" / "live" / "labs.example.com"
        live.mkdir(parents=True)
        (live / "fullchain.pem").write_text("CHAIN-2\n", encoding="utf-8")
        (live / "privkey.pem").write_text("KEY-2\n", encoding="utf-8")
        out = tmp / "router-certs"
        env = {**os.environ, "LETSENCRYPT_DIR": (tmp / "le").as_posix(), "ROUTER_CERT_DIR": out.as_posix(),
               "ROUTER_CONTAINER": f"no-such-router-{uuid.uuid4().hex[:8]}"}
        env.pop("RENEWED_LINEAGE", None)
        if lineage is not None:
            env["RENEWED_LINEAGE"] = (tmp / "le" / "live" / lineage).as_posix()
        result = subprocess.run([BASH, HOOK.as_posix(), "labs.example.com"], capture_output=True, text=True,
                                env=env, timeout=60)
        return result, out

    def test_copies_the_lab_certificate(self) -> None:
        for lineage in (None, "labs.example.com"):
            result, out = self._run(lineage)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out / "fullchain.pem").read_text(encoding="utf-8"), "CHAIN-2\n")
            self.assertEqual((out / "privkey.pem").read_text(encoding="utf-8"), "KEY-2\n")
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["fullchain.pem", "privkey.pem"])

    def test_ignores_another_certificate(self) -> None:
        result, out = self._run("other.example.com")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(out.exists())


def _docker_ready() -> bool:
    if not DOCKER:
        return False
    try:
        return _docker("info", "--format", "{{.ServerVersion}}", timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@unittest.skipUnless(_docker_ready(), "no Docker daemon")
class LiveRouterTests(unittest.TestCase):
    """The real router config, with the cloud switches, in nginx:alpine."""

    TOKEN = "test-token-" + uuid.uuid4().hex

    @classmethod
    def setUpClass(cls) -> None:
        if _docker("image", "inspect", IMAGE).returncode != 0 and _docker("pull", IMAGE, timeout=300).returncode:
            raise unittest.SkipTest(f"cannot pull {IMAGE}")
        cls.tmp = Path(tempfile.mkdtemp(prefix="acme-live."))
        challenge = cls.tmp / ".well-known" / "acme-challenge"
        challenge.mkdir(parents=True)
        (challenge / cls.TOKEN).write_text("proof-" + cls.TOKEN, encoding="utf-8")
        mounts = {
            ROUTER / "nginx-ssl.conf": "/etc/nginx/conf.d/default.conf",
            ROUTER / "nginx-cache.conf": "/etc/nginx/conf.d/00-cache.conf",
            ROUTER / "nginx-maps.conf": "/etc/nginx/conf.d/10-maps.conf",
            ROUTER / "routes.conf": "/etc/nginx/routes.conf",
            ROUTER / "routes": "/etc/nginx/routes",
            ROUTER / "class-gate" / "on.conf": "/etc/nginx/class-gate.conf",
            ROUTER / "https-redirect" / "on.conf": "/etc/nginx/https-redirect.conf",
            ROUTER / "certs": "/etc/nginx/certs",
            cls.tmp: "/var/www/acme",
        }
        cls.name = f"acme-challenge-test-{uuid.uuid4().hex[:8]}"
        args = ["run", "-d", "--rm", "--name", cls.name, "-p", "127.0.0.1::80"]
        for source, target in mounts.items():
            args += ["--mount", f"type=bind,source={source},target={target},readonly"]
        started = _docker(*args, IMAGE, timeout=120)
        if started.returncode:
            shutil.rmtree(cls.tmp, True)
            raise AssertionError(f"router container did not start: {started.stderr.strip()[:400]}")
        cls.port = cls._wait_for_port()

    @classmethod
    def tearDownClass(cls) -> None:
        _docker("rm", "-f", cls.name)
        shutil.rmtree(cls.tmp, True)

    @classmethod
    def _wait_for_port(cls) -> int:
        for _ in range(40):
            mapped = _docker("port", cls.name, "80/tcp").stdout.strip().splitlines()
            if mapped:
                port = int(mapped[0].rsplit(":", 1)[1])
                try:
                    cls._get(port, "localhost", "/")
                    return port
                except OSError:
                    pass
            time.sleep(0.5)
        logs = _docker("logs", cls.name).stderr[-800:]
        _docker("rm", "-f", cls.name)
        raise AssertionError(f"router did not answer on port 80: {logs}")

    @staticmethod
    def _get(port: int, host: str, path: str) -> tuple[int, dict[str, str], str]:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        try:
            conn.request("GET", path, headers={"Host": host})
            response = conn.getresponse()
            return response.status, {k.lower(): v for k, v in response.getheaders()}, response.read().decode()
        finally:
            conn.close()

    def test_config_passes_nginx_t(self) -> None:
        result = _docker("exec", self.name, "nginx", "-t")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_challenge_is_served_on_every_host_without_redirect_or_class_code(self) -> None:
        for host in ("labs.example.com", "explorer.labs.example.com", "tokens.labs.example.com",
                     "dex.labs.example.com", "dex-l2.labs.example.com"):
            status, headers, body = self._get(self.port, host, f"/.well-known/acme-challenge/{self.TOKEN}")
            self.assertEqual((status, body), (200, "proof-" + self.TOKEN), (host, headers))
            self.assertNotIn("location", headers, host)

    def test_missing_token_is_404_not_a_redirect(self) -> None:
        status, headers, _ = self._get(self.port, "labs.example.com", "/.well-known/acme-challenge/nope")
        self.assertEqual(status, 404)
        self.assertNotIn("location", headers)

    def test_other_plain_http_still_redirects(self) -> None:
        for host, path in (("labs.example.com", "/labs/bitcoin/"), ("labs.example.com", "/class"),
                           ("explorer.labs.example.com", "/"), ("labs.example.com", "/.well-known/other"),
                           ("labs.example.com", "/x/.well-known/acme-challenge/" + self.TOKEN)):
            status, headers, _ = self._get(self.port, host, path)
            self.assertEqual(status, 301, (host, path))
            self.assertEqual(headers.get("location"), f"https://{host}{path}")


if __name__ == "__main__":
    unittest.main()
