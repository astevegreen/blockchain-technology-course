"""What the student's computer offers: Docker version, memory, processor, free ports, internet, updates."""
from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from typing import Callable

from .docker_cli import Docker

# design section 2.1: 80 falls back to 8480; 8441-8444 are fixed (the explorer redirect needs host = container port).
HTTP_PORTS = (80, 8480)
LAB_PORTS = (8441, 8442, 8443, 8444)
ALL_PORTS = HTTP_PORTS + LAB_PORTS
BUSY = re.compile(r"port is already allocated|address already in use|bind: ", re.I)

ARCH_PLATFORM = {"x86_64": "linux/amd64", "amd64": "linux/amd64", "aarch64": "linux/arm64", "arm64": "linux/arm64"}
ARCH_NAME = {"linux/amd64": "Intel or AMD", "linux/arm64": "Apple silicon or ARM"}

REGISTRY = "ghcr.io"
REPOSITORY = "astevegreen/course-labs"
STABLE_TAG = "launcher-stable"
MANIFEST_TYPES = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


def platform_of(info: dict | None) -> str | None:
    if not info:
        return None
    return ARCH_PLATFORM.get(str(info.get("Architecture", "")).lower())


def memory_mb(info: dict | None) -> int | None:
    if not info or not info.get("MemTotal"):
        return None
    return int(info["MemTotal"]) // (1024 * 1024)


def internet_reachable(host: str = REGISTRY, port: int = 443, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class PortProbe:
    """Whether a host port is free, asked of the Docker daemon: the control container can't see host ports itself.

    It publishes the port on 127.0.0.1 with a throwaway container of the launcher's own image (already present).
    Ports a course container already publishes count as ours, not busy.
    """

    def __init__(self, docker: Docker, image: Callable[[], str]):
        self.docker = docker
        self.image = image

    def ours(self) -> set[int]:
        ports = set()
        for row in self.docker.containers("label=course.lab"):
            if row.get("State") != "running":
                continue
            for match in re.finditer(r":(\d+)(?:-(\d+))?->", row.get("Ports", "")):
                low = int(match.group(1))
                high = int(match.group(2) or low)
                ports.update(range(low, high + 1))
        return ports

    def free(self, port: int) -> bool | None:
        image = self.image()
        if not image:
            return None
        result = self.docker.run("run", "--rm", "--entrypoint", "true", "-p", f"127.0.0.1:{port}:9", image,
                                 timeout=60)
        if result.ok:
            return True
        return False if BUSY.search(result.out) else None

    def check(self, ports=ALL_PORTS) -> dict[int, str]:
        """port -> "free", "busy", "course" (a course container has it) or "unknown"."""
        ours = self.ours()
        status = {}
        for port in ports:
            if port in ours:
                status[port] = "course"
                continue
            free = self.free(port)
            status[port] = "unknown" if free is None else ("free" if free else "busy")
        return status


def registry_digest(tag: str = STABLE_TAG, opener=urllib.request.urlopen, timeout: float = 10.0) -> str | None:
    """The digest ghcr serves for course-labs:<tag>, asked anonymously (the package is public)."""
    try:
        token_url = f"https://{REGISTRY}/token?scope=repository:{REPOSITORY}:pull&service={REGISTRY}"
        with opener(token_url, timeout=timeout) as resp:
            token = json.loads(resp.read().decode("utf-8")).get("token", "")
        req = urllib.request.Request(f"https://{REGISTRY}/v2/{REPOSITORY}/manifests/{tag}", method="HEAD",
                                     headers={"Authorization": f"Bearer {token}", "Accept": MANIFEST_TYPES})
        with opener(req, timeout=timeout) as resp:
            return resp.headers.get("Docker-Content-Digest")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def running_digests(docker: Docker, image: str) -> list[str]:
    """The registry digests of the image the control container runs (`RepoDigests`, `repo@sha256:...`)."""
    if not image:
        return []
    result = docker.run("image", "inspect", "--format", "{{json .RepoDigests}}", image, timeout=60)
    if not result.ok:
        return []
    try:
        return [d.split("@", 1)[1] for d in json.loads(result.out.strip() or "[]") if "@" in d]
    except json.JSONDecodeError:
        return []
