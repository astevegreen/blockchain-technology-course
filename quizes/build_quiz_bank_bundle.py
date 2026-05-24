#!/usr/bin/env python3
"""Build a JSON-list quiz-bank bundle for instructor import."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _validate_bank(path: Path, data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    lesson_id = str(data.get("lesson_id") or "").strip()
    if not lesson_id:
        raise ValueError(f"{path}: missing lesson_id")
    lesson_title = str(data.get("lesson_title") or "").strip()
    if not lesson_title:
        raise ValueError(f"{path}: missing lesson_title")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError(f"{path}: questions must be a non-empty list")
    for idx, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"{path}: question {idx} must be an object")
        stem = str(question.get("question_stem") or question.get("question") or "").strip()
        if not stem:
            raise ValueError(f"{path}: question {idx} missing question_stem")
    return data


def build_bundle(quiz_dir: Path) -> list[dict]:
    files = sorted(quiz_dir.glob("*-quiz-bank.json"))
    if not files:
        raise ValueError(f"No quiz-bank JSON files found in {quiz_dir}")

    bundle: list[dict] = []
    seen: set[str] = set()
    for path in files:
        if "course_welcome" in path.name:
            raise ValueError(f"{path}: course_welcome quiz should not be bundled")
        data = _validate_bank(path, json.loads(path.read_text(encoding="utf-8")))
        lesson_id = str(data["lesson_id"]).strip()
        if lesson_id in seen:
            raise ValueError(f"{path}: duplicate lesson_id {lesson_id}")
        seen.add(lesson_id)
        bundle.append(data)
    return bundle


def main() -> int:
    root = _repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiz-dir",
        type=Path,
        default=root / "quizes" / "quiz_json",
        help="Directory containing *-quiz-bank.json files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "quizes" / "dist" / "blockchain-course-quiz-bank-bundle.json",
        help="Output JSON-list bundle path.",
    )
    args = parser.parse_args()

    quiz_dir = args.quiz_dir.resolve()
    output = args.output.resolve()
    bundle = build_bundle(quiz_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_questions = sum(len(bank.get("questions") or []) for bank in bundle)
    print(f"Wrote {len(bundle)} quiz banks / {total_questions} questions to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
