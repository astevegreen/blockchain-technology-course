"""The runtime secrets env file, generated the way dynamic-labs/runtime-credentials.sh does it.

Local mode writes every variable runtime-credentials.sh writes, with the same generators, so any launcher compose
file's `${X:?}` finds its value. No instructor-credentials file: local mode has no instructor surfaces.
Values persist on the state volume; a release that adds a secret fills in only the missing one.
"""
from __future__ import annotations

import os
import secrets
import string
from pathlib import Path
from typing import Callable

ALNUM = string.ascii_letters + string.digits
# runtime_class_code: no 0/O or 1/I/L.
CLASS_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def random_alnum(length: int) -> str:
    return "".join(secrets.choice(ALNUM) for _ in range(length))


def random_hex(nbytes: int) -> str:
    return secrets.token_hex(nbytes)


def class_code() -> str:
    return "".join(secrets.choice(CLASS_CODE_ALPHABET) for _ in range(8))


# In runtime-credentials.sh's order. A generator takes the values made so far (two copy another value).
GENERATORS: dict[str, Callable[[dict[str, str]], str]] = {
    "QUIZ_ENGINE_SECRET_KEY": lambda v: random_hex(32),
    "QUIZ_ENGINE_INSTRUCTOR_PASSWORD": lambda v: random_alnum(24),
    "BGP_GAME_SECRET_KEY": lambda v: random_hex(32),
    "BGP_GAME_INSTRUCTOR_USER": lambda v: "instructor",
    "BGP_GAME_INSTRUCTOR_PASS": lambda v: random_alnum(20),
    "TRUST_GAME_SECRET_KEY": lambda v: random_hex(32),
    "TRUST_GAME_INSTRUCTOR_USERNAME": lambda v: "instructor",
    "TRUST_GAME_INSTRUCTOR_PASSWORD": lambda v: random_alnum(20),
    "INSTRUCTOR_AUTH_USER": lambda v: v.get("TRUST_GAME_INSTRUCTOR_USERNAME") or "instructor",
    "INSTRUCTOR_AUTH_KEY": lambda v: v.get("TRUST_GAME_INSTRUCTOR_PASSWORD") or random_alnum(20),
    "INSTRUCTOR_AUTH_SERVICE_SECRET_KEY": lambda v: random_hex(32),
    "HLF_WEB_SECRET_KEY": lambda v: random_hex(32),
    "LANE_SERVICE_SECRET": lambda v: random_hex(32),
    "HOSTING_RUNNER_SECRET": lambda v: random_hex(32),
    "HLF_CA_ADMIN_PASSWORD": lambda v: random_alnum(24),
    "HLF_COUCHDB_PASSWORD": lambda v: random_alnum(24),
    "CLASS_CODE": lambda v: class_code(),
}


def read_env(path: Path) -> dict[str, str]:
    values = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def ensure(path: Path) -> dict[str, str]:
    """Read the env file, generate whatever is missing, write it back (mode 600) and return every value."""
    values = read_env(path)
    changed = False
    for name, make in GENERATORS.items():
        if not values.get(name):
            values[name] = make(values)
            changed = True
    if changed or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, path)
    return values
