"""Tests for tools/lab_images.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_images  # noqa: E402


class ComposeImages(unittest.TestCase):
    def test_a_service_that_builds_its_image_pulls_nothing(self) -> None:
        text = """
services:
  lab:
    build: .
    image: bitcoin-lab-student
  mempool:
    image: "${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/blockchain-course-2026/bitcoin-mempool:latest}"
  web:
    image: nginx:alpine
  odd:
    image: ${NO_DEFAULT}
"""
        pulled, built = lab_images.compose_images(text)
        self.assertEqual(pulled, {"ghcr.io/blockchain-course-2026/bitcoin-mempool:latest", "nginx:alpine"})
        self.assertEqual(built, {"bitcoin-lab-student"})

    def test_a_file_with_no_services_has_no_images(self) -> None:
        self.assertEqual(lab_images.compose_images("version: '3'\n"), (set(), set()))


class DockerfileImages(unittest.TestCase):
    def test_stages_scratch_and_platform_flags(self) -> None:
        text = """
FROM --platform=linux/amd64 docker:27-cli AS docker_cli
FROM python:3.11-slim
COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker
FROM docker_cli
FROM scratch
"""
        self.assertEqual(lab_images.dockerfile_images(text), {"docker:27-cli", "python:3.11-slim"})

    def test_arg_defaults_fill_variables_and_a_variable_with_none_is_left_out(self) -> None:
        text = "ARG BITCOIN_LAB_BASE=ghcr.io/blockchain-course-2026/bitcoin-lab:latest\nFROM ${BITCOIN_LAB_BASE}\n"
        self.assertEqual(lab_images.dockerfile_images(text), {"ghcr.io/blockchain-course-2026/bitcoin-lab:latest"})
        self.assertEqual(lab_images.dockerfile_images("FROM hyperledger/fabric-${ROLE}:${VERSION}\n"), set())


class Repo(unittest.TestCase):
    def test_the_labs_pull_the_images_that_stalled_25_oct_and_no_local_build(self) -> None:
        images = lab_images.lab_images()
        for image in ("python:3.11-slim", "docker:27-cli", "ghcr.io/blockchain-course-2026/bitcoin-lab:latest"):
            self.assertIn(image, images)
        for local in ("lane-service:latest", "hlf-peer-ttyd:latest", "bitcoin-lab-student"):
            self.assertNotIn(local, images)


class Pull(unittest.TestCase):
    def test_each_image_gets_three_tries_and_the_failures_are_named(self) -> None:
        calls: list[str] = []

        def run(cmd: list[str]) -> int:
            calls.append(cmd[-1])
            return 0 if cmd[-1] == "ok:1" or (cmd[-1] == "flaky:1" and calls.count("flaky:1") == 2) else 1

        self.assertEqual(lab_images.pull_all(["ok:1", "flaky:1", "down:1"], run), ["down:1"])
        self.assertEqual(calls, ["ok:1", "flaky:1", "flaky:1", "down:1", "down:1", "down:1"])


if __name__ == "__main__":
    unittest.main()
