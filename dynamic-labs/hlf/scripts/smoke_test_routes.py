#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.request


ROUTES = [
    ("html", "http://127.0.0.1:8081/labs/hlf/"),
    ("html", "http://127.0.0.1:8081/labs/hlf/instructor/"),
    ("html", "http://127.0.0.1:8081/labs/hlf/explorer/"),
    ("html", "http://127.0.0.1:8081/labs/hlf/exercises/"),
    ("json", "http://127.0.0.1:8081/labs/hlf/api/hlf/status"),
    ("json", "http://127.0.0.1:8081/labs/hlf/api/hlf/health"),
    ("json", "http://127.0.0.1:8081/labs/hlf/api/hlf/instructor-snapshot?lines=15"),
    ("json", "http://127.0.0.1:8081/labs/hlf/api/hlf/explorer-view"),
]


def main() -> int:
    failures = 0
    for expected, url in ROUTES:
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                body = response.read().decode("utf-8", errors="ignore")
                content_type = response.headers.get_content_type()
                status = response.status
            if expected == "json":
                json.loads(body)
            print(f"OK {status} {content_type} {url}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {url} {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
