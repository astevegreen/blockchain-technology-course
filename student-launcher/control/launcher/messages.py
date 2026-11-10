"""Plain-language messages. Students are not technical: the page never shows a raw Docker error on its own."""
from __future__ import annotations

import re

DOCKER_SETTINGS = "Open Docker Desktop, choose Settings, then Resources"

NO_INTERNET = ("No internet connection. The first start of each lab downloads it, so connect to the internet and "
               "press Start again.")
NO_DISK = ("Your computer is out of disk space for this lab. Free some space (or press Reset on labs you have "
           "finished), then press Start again.")
NOT_PUBLISHED = ("This lab's download isn't available yet. Tell your instructor: the course images may not be "
                 "public.")
ISOLATION = ("Docker Desktop's \"Enhanced Container Isolation\" setting is blocking the labs. It is set by your "
             "organisation's Docker administrator; ask them to turn it off for this computer.")
CLASSROOM = ("This computer is already running the course labs another way (the classroom setup). Stop those labs "
             "first, then close this page and double-click Start Course Labs again.")
NOT_ON_THIS_COMPUTER = "This lab isn't available for this computer's processor ({arch})."
GENERIC = "Something went wrong while {doing}. Press Start to try again. If it happens again, tell your instructor."


def docker_too_old(desktop: str) -> str:
    return (f"This lab needs Docker Desktop {desktop} or newer. Update Docker Desktop, then press Start again.")


def memory_short(have_mb: int, need_mb: int) -> str:
    return (f"Docker has {gb(have_mb)} of memory but this lab needs {gb(need_mb)}. {DOCKER_SETTINGS}, and raise "
            f"Memory to at least {gb(need_mb)}.")


def port_busy(port: int) -> str:
    return (f"Port {port} is busy: another program on this computer is using it. Close that program (or restart the "
            f"computer), then press Start again.")


def ports_busy(ports: list[int]) -> str:
    listed = " and ".join(str(p) for p in ports)
    return (f"Ports {listed} are both busy: other programs on this computer are using them. Close them (or restart "
            f"the computer), then press Start again.")


def gb(mb: int) -> str:
    value = mb / 1024
    return f"{value:.0f} GB" if value >= 10 or value == int(value) else f"{value:.1f} GB"


NETWORK_PATTERNS = re.compile(r"dial tcp|no such host|i/o timeout|TLS handshake timeout|network is unreachable|"
                              r"connection refused|temporary failure in name resolution|EOF$", re.I | re.M)


def explain(output: str, doing: str) -> str:
    """Turn a docker or compose error into one sentence a student can act on."""
    text = output or ""
    port = re.search(r"(?:0\.0\.0\.0|127\.0\.0\.1|\[::\]|:::?)?:(\d+).*?(?:port is already allocated|address "
                     r"already in use)|Bind for [\d.:]+?:(\d+) failed", text, re.I)
    if port or re.search(r"port is already allocated|address already in use", text, re.I):
        number = next((g for g in (port.groups() if port else ()) if g), None)
        return port_busy(int(number)) if number else port_busy(80)
    if re.search(r"no space left on device", text, re.I):
        return NO_DISK
    if re.search(r"enhanced container isolation", text, re.I):
        return ISOLATION
    if re.search(r"denied|unauthorized|manifest unknown|not found: manifest|manifest for .* not found", text, re.I):
        return NOT_PUBLISHED
    if NETWORK_PATTERNS.search(text):
        return NO_INTERNET
    return GENERIC.format(doing=doing)
