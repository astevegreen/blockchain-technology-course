"""The HLF helper images in launcher mode: the orderer Dockerfile, the release images and the course labels.

The release builds each Dockerfile once (tools/student_release.py) with no build args, so the orderer image has its
own Dockerfile and the ttyd binaries follow the build platform. lab.sh tags the release images for the compose
files, and volume_binds.py --release labels every Fabric container the way the launcher stack labels its own.
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HLF = ROOT / "hlf"
sys.path.insert(0, str(HLF / "managed_runtime"))
sys.modules.pop("volume_binds", None)

import volume_binds  # noqa: E402


def services(text: str) -> dict:
    return yaml.safe_load(text)["services"]


class OrdererDockerfile(unittest.TestCase):
    def test_it_is_the_peer_file_with_the_orderer_role(self):
        peer = (HLF / "Dockerfile.ttyd").read_text(encoding="utf-8").splitlines()
        orderer = (HLF / "Dockerfile.orderer-ttyd").read_text(encoding="utf-8").splitlines()
        strip = lambda lines: [ln for ln in lines if not ln.startswith("#")]  # noqa: E731
        self.assertEqual([ln.replace("FABRIC_ROLE=peer", "FABRIC_ROLE=orderer") for ln in strip(peer)],
                         strip(orderer), "copy Dockerfile.ttyd to Dockerfile.orderer-ttyd, role orderer")
        self.assertIn("ARG FABRIC_ROLE=orderer", orderer)

    def test_the_ttyd_arch_defaults_to_the_build_platform(self):
        text = (HLF / "Dockerfile.ttyd").read_text(encoding="utf-8")
        self.assertIn("ARG TTYD_ARCH=\n", text)
        self.assertIn('arch="${TTYD_ARCH:-$(uname -m)}"', text)
        self.assertNotRegex(text, r"(?m)^ADD ", "a download in ADD can't follow uname -m")

    def test_the_release_and_the_builds_use_it(self):
        lab = yaml.safe_load((HLF / "lab.yaml").read_text(encoding="utf-8"))
        self.assertEqual(lab["services"]["hlf-orderer-ttyd"]["dockerfile"], "Dockerfile.orderer-ttyd")
        self.assertEqual(lab["services"]["hlf-peer-ttyd"]["dockerfile"], "Dockerfile.ttyd")
        compose = yaml.safe_load((HLF / "docker-compose.yml").read_text(encoding="utf-8"))
        self.assertEqual(compose["services"]["hlf-orderer-ttyd"]["build"]["dockerfile"], "Dockerfile.orderer-ttyd")
        for name in ("Dockerfile", "Dockerfile.launcher"):
            self.assertIn("COPY Dockerfile.orderer-ttyd /opt/hlf/Dockerfile.orderer-ttyd",
                          (HLF / name).read_text(encoding="utf-8"), name)
        lab_sh = (HLF / "lab.sh").read_text(encoding="utf-8")
        self.assertIn('-f "${ttyd_ctx}/Dockerfile.orderer-ttyd"', lab_sh)
        self.assertIn('cp -f "${HERE}/Dockerfile.orderer-ttyd"', lab_sh)


class ReleaseHelperImages(unittest.TestCase):
    def test_lab_sh_tags_each_release_image_before_it_builds(self):
        lab_sh = (HLF / "lab.sh").read_text(encoding="utf-8")
        body = lab_sh[lab_sh.index("use_release_helper_images() {"):lab_sh.index("build_ttyd_images() {")]
        for var, tag in (("HLF_HLF_PEER_TTYD_IMAGE", "hlf-peer-ttyd"),
                         ("HLF_HLF_ORDERER_TTYD_IMAGE", "hlf-orderer-ttyd"),
                         ("HLF_CHAINCODE_BASIC_IMAGE", "chaincode-basic")):
            self.assertIn(f'{tag}) ref="${{{var}:-}}"', body)
        self.assertIn('docker tag "${ref}" "${local_tag}:latest"', body)
        build = lab_sh[lab_sh.index("build_ttyd_images() {"):]
        self.assertTrue(build.splitlines()[1].strip() == "use_release_helper_images")

    def test_the_launcher_passes_the_release_to_the_runner(self):
        compose = yaml.safe_load((HLF / "docker-compose.launcher.yml").read_text(encoding="utf-8"))
        env = compose["services"]["hlf-runner"]["environment"]
        for var in ("COURSE_RELEASE", "HLF_HLF_PEER_TTYD_IMAGE", "HLF_HLF_ORDERER_TTYD_IMAGE",
                    "HLF_CHAINCODE_BASIC_IMAGE"):
            self.assertIn(var, env)
            self.assertTrue(str(env[var]).startswith("${" + var + ":-"), f"{var}: {env[var]}")


class CourseLabels(unittest.TestCase):
    SAMPLE = """# comment
services:
  orderer.example.com:
    image: hlf-orderer-ttyd:latest
    labels:
      service: hyperledger-fabric
    environment:
      - A=1
  peer0.org1.example.com:
    image: hlf-peer-ttyd:latest
    environment:
      - B=2
networks:
  test:
    name: fabric_test
"""

    def test_every_service_gets_both_labels(self):
        out = services(volume_binds.add_labels(self.SAMPLE, "hlf", "v1.2.3"))
        for name, svc in out.items():
            self.assertEqual(svc["labels"]["course.lab"], "hlf", name)
            self.assertEqual(svc["labels"]["course.release"], "v1.2.3", name)
        self.assertEqual(out["orderer.example.com"]["labels"]["service"], "hyperledger-fabric")
        self.assertEqual(out["peer0.org1.example.com"]["environment"], ["B=2"])

    def test_it_is_idempotent_and_a_new_release_replaces_the_old(self):
        once = volume_binds.add_labels(self.SAMPLE, "hlf", "dev")
        self.assertEqual(volume_binds.add_labels(once, "hlf", "dev"), once)
        again = services(volume_binds.add_labels(once, "hlf", "regression"))
        self.assertEqual({s["labels"]["course.release"] for s in again.values()}, {"regression"})

    def test_networks_and_volumes_are_left_alone(self):
        out = yaml.safe_load(volume_binds.add_labels(self.SAMPLE, "hlf", "dev"))
        self.assertEqual(out["networks"], {"test": {"name": "fabric_test"}})

    def test_every_generated_compose_file_is_labelled(self):
        templates = sorted((HLF / "managed_runtime").glob("compose-*.yaml.tmpl"))
        self.assertTrue(templates)
        for path in templates:
            text = re.sub(r"\$\{[^}]*\}", "x", path.read_text(encoding="utf-8"))
            out = services(volume_binds.add_labels(text, "hlf", "dev"))
            for name, svc in out.items():
                self.assertEqual(svc["labels"]["course.release"], "dev", f"{path.name}: {name}")

    def test_the_cli_refuses_a_bad_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "c.yaml"
            f.write_text(self.SAMPLE, encoding="utf-8")
            argv = sys.argv
            sys.argv = ["volume_binds.py", "--volume", "v", "--root", tmp, "--release", "bad value", str(f)]
            try:
                with self.assertRaises(SystemExit):
                    volume_binds.main()
            finally:
                sys.argv = argv


if __name__ == "__main__":
    unittest.main()
