from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "ethereum_lab"


def _pattern_regex(pattern: str) -> re.Pattern[str]:
    # Docker's .dockerignore rules: "*" and "?" stop at "/", "**" spans folders.
    out = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z")


def _rules() -> list[tuple[bool, re.Pattern[str]]]:
    rules = []
    for line in (LAB / ".dockerignore").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        rules.append((negate, _pattern_regex(line.lstrip("!").strip("/"))))
    return rules


def _ignored(rel: str, rules: list[tuple[bool, re.Pattern[str]]]) -> bool:
    # A pattern also matches everything under a folder it matches; the last matching rule wins.
    parts = rel.split("/")
    candidates = ["/".join(parts[:n]) for n in range(1, len(parts) + 1)]
    ignored = False
    for negate, regex in rules:
        if any(regex.match(c) for c in candidates):
            ignored = not negate
    return ignored


class EthereumLabDockerContextTests(unittest.TestCase):
    def test_instructor_guides_stay_out_of_the_image(self) -> None:
        rules = _rules()
        guides = [
            path.relative_to(LAB).as_posix()
            for folder in ("docs/instructor", "frontend/public/docs/instructor")
            for path in (LAB / folder).rglob("*")
            if path.is_file()
        ]
        self.assertTrue(guides, "expected instructor guides to check")
        leaked = [rel for rel in guides if not _ignored(rel, rules)]
        self.assertEqual(leaked, [], "instructor guides reach the Docker build context")

    def test_lab_docs_the_gui_loads_stay_in_the_image(self) -> None:
        rules = _rules()
        labs = (LAB / "frontend/src/constants/labs.js").read_text(encoding="utf-8")
        docs = [f"docs/{doc}.md" for doc in re.findall(r"doc:\s*'([^']+)'", labs)]
        self.assertTrue(docs, "expected lab docs in labs.js")
        for rel in docs:
            self.assertTrue((LAB / rel).is_file(), rel)
            self.assertFalse(_ignored(rel, rules), f"{rel} is left out of the Docker build")


if __name__ == "__main__":
    unittest.main()
