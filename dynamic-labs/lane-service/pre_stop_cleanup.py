#!/usr/bin/env python3
"""
Best-effort lane cleanup for Docker Compose pre_stop.

The main lane-service process already traps SIGTERM/SIGINT and calls the
same stop handlers. This entrypoint exists as a separate pre_stop hook so
`docker compose down` gets an additional cleanup pass before the process is
signaled.
"""

from labs import bitcoin, consensus, cryptography, ethereum, p2p_trust


def main() -> int:
    for module in (bitcoin, consensus, p2p_trust, ethereum, cryptography):
        stop = getattr(module, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception as exc:
                print(f"[lane-service pre-stop] {module.__name__}.stop failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
