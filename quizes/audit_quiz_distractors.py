#!/usr/bin/env python3
"""Audit offline quiz-bank distractor structure and answer-length leakage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


SMELL_RE = re.compile(
    r"\b(always|never|automatically|guarantees?|impossible|cannot ever|"
    r"all blockchains|all transactions|instantly final|fully anonymous)\b",
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str
    file: str
    question_id: str
    message: str


def _quiz_files(quiz_dir: Path) -> list[Path]:
    return sorted(quiz_dir.glob("*-quiz-bank.json"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def _target_count(total_questions: int) -> int:
    return round(total_questions * 0.25)


def _classify(correct_len: int, incorrect_lens: list[int]) -> str:
    if not incorrect_lens:
        return "invalid"
    if correct_len > max(incorrect_lens):
        return "longest"
    if correct_len < min(incorrect_lens):
        return "shortest"
    if any(length > correct_len for length in incorrect_lens) and any(
        length < correct_len for length in incorrect_lens
    ):
        return "middle"
    return "tie"


def build_baseline(quiz_dir: Path) -> dict[str, Any]:
    files = {}
    for path in _quiz_files(quiz_dir):
        data = _load_json(path)
        files[path.name] = {
            str(q.get("id")): {
                "question_stem": q.get("question_stem"),
                "correct_answer": q.get("correct_answer"),
                "question_type": q.get("question_type", "multiple_choice"),
            }
            for q in data.get("questions", [])
        }
    return {"schema_version": 1, "files": files}


def _baseline_question(
    baseline: dict[str, Any] | None, file_name: str, question_id: str
) -> dict[str, Any] | None:
    if not baseline:
        return None
    return (
        baseline.get("files", {})
        .get(file_name, {})
        .get(str(question_id))
    )


def audit_file(
    path: Path,
    *,
    baseline: dict[str, Any] | None,
    length_margin: float,
) -> tuple[list[Finding], dict[str, Any]]:
    data = _load_json(path)
    findings: list[Finding] = []
    questions = data.get("questions", [])
    length_classes = {"longest": 0, "shortest": 0, "middle": 0, "tie": 0, "invalid": 0}
    correct_lengths: list[int] = []
    incorrect_lengths: list[int] = []
    edited_questions = 0

    if not isinstance(questions, list) or not questions:
        findings.append(Finding("error", path.name, "-", "questions must be non-empty"))
        return findings, {"questions": 0}

    for q in questions:
        qid = str(q.get("id") or "?")
        question_type = q.get("question_type", "multiple_choice")
        if question_type != "multiple_choice":
            continue

        correct = q.get("correct_answer")
        incorrect = q.get("incorrect_answers")
        if not isinstance(correct, str) or not correct.strip():
            findings.append(Finding("error", path.name, qid, "missing correct_answer"))
            continue
        if not isinstance(incorrect, list) or len(incorrect) < 2:
            findings.append(Finding("error", path.name, qid, "too few incorrect_answers"))
            continue
        if not all(isinstance(item, str) and item.strip() for item in incorrect):
            findings.append(Finding("error", path.name, qid, "blank/non-text distractor"))
            continue

        baseline_q = _baseline_question(baseline, path.name, qid)
        if baseline_q:
            if q.get("question_stem") != baseline_q.get("question_stem"):
                findings.append(Finding("error", path.name, qid, "question_stem changed"))
            if correct != baseline_q.get("correct_answer"):
                findings.append(Finding("error", path.name, qid, "correct_answer changed"))
            if question_type != baseline_q.get("question_type"):
                findings.append(Finding("error", path.name, qid, "question_type changed"))

        normalized_options = [_norm(correct), *[_norm(item) for item in incorrect]]
        if len(normalized_options) != len(set(normalized_options)):
            findings.append(Finding("error", path.name, qid, "duplicate option text"))
        if _norm(correct) in {_norm(item) for item in incorrect}:
            findings.append(Finding("error", path.name, qid, "correct answer appears as distractor"))

        correct_len = len(correct)
        inc_lens = [len(item) for item in incorrect]
        correct_lengths.append(correct_len)
        incorrect_lengths.extend(inc_lens)
        length_classes[_classify(correct_len, inc_lens)] += 1

        for idx, item in enumerate(incorrect, start=1):
            deviation = abs(len(item) - correct_len) / correct_len if correct_len else 0
            if deviation > length_margin:
                findings.append(
                    Finding(
                        "warn",
                        path.name,
                        qid,
                        f"distractor {idx} length differs from correct by {deviation:.0%}",
                    )
                )
            if SMELL_RE.search(item):
                findings.append(
                    Finding(
                        "warn",
                        path.name,
                        qid,
                        f"distractor {idx} contains likely giveaway wording",
                    )
                )

        if baseline_q:
            # Count as edited if any distractor differs. This is informational:
            # a worker may reasonably leave good existing distractors unchanged.
            edited_questions += 1

    target_longest = _target_count(len(questions))
    target_shortest = _target_count(len(questions))
    target_middle = len(questions) - target_longest - target_shortest
    if length_classes["longest"] != target_longest:
        findings.append(
            Finding(
                "error",
                path.name,
                "-",
                f"correct-longest count {length_classes['longest']} != target {target_longest}",
            )
        )
    if length_classes["shortest"] != target_shortest:
        findings.append(
            Finding(
                "error",
                path.name,
                "-",
                f"correct-shortest count {length_classes['shortest']} != target {target_shortest}",
            )
        )
    if length_classes["middle"] != target_middle:
        findings.append(
            Finding(
                "error",
                path.name,
                "-",
                f"correct-middle count {length_classes['middle']} != target {target_middle}",
            )
        )
    if length_classes["tie"]:
        findings.append(
            Finding("error", path.name, "-", f"{length_classes['tie']} length tie classifications")
        )

    stats = {
        "questions": len(questions),
        "length_classes": length_classes,
        "avg_correct_len": mean(correct_lengths) if correct_lengths else 0,
        "avg_incorrect_len": mean(incorrect_lengths) if incorrect_lengths else 0,
        "edited_questions": edited_questions,
    }
    return findings, stats


def print_report(all_findings: list[Finding], stats_by_file: dict[str, dict[str, Any]]) -> int:
    total_questions = sum(stats.get("questions", 0) for stats in stats_by_file.values())
    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warn"]

    print("=== QUIZ DISTRACTOR AUDIT ===")
    print(f"Files:     {len(stats_by_file)}")
    print(f"Questions: {total_questions}")
    print(f"Errors:    {len(errors)}")
    print(f"Warnings:  {len(warnings)}")
    print()

    for file_name, stats in stats_by_file.items():
        classes = stats.get("length_classes", {})
        print(
            f"{file_name}: q={stats.get('questions', 0)} "
            f"L/S/M/T={classes.get('longest', 0)}/"
            f"{classes.get('shortest', 0)}/{classes.get('middle', 0)}/"
            f"{classes.get('tie', 0)} "
            f"avg={stats.get('avg_correct_len', 0):.1f}/"
            f"{stats.get('avg_incorrect_len', 0):.1f}"
        )

    if all_findings:
        print("\nFindings:")
        for finding in all_findings[:300]:
            print(
                f"- {finding.severity.upper()} {finding.file} {finding.question_id}: "
                f"{finding.message}"
            )
        if len(all_findings) > 300:
            print(f"... {len(all_findings) - 300} more findings omitted")

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiz-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "quiz_json",
    )
    parser.add_argument("--write-baseline", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--length-margin", type=float, default=0.10)
    args = parser.parse_args()

    quiz_dir = args.quiz_dir.resolve()
    if args.write_baseline:
        baseline = build_baseline(quiz_dir)
        args.write_baseline.write_text(
            json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote baseline to {args.write_baseline}")
        return 0

    baseline = None
    if args.baseline:
        baseline = _load_json(args.baseline)

    all_findings: list[Finding] = []
    stats_by_file: dict[str, dict[str, Any]] = {}
    for path in _quiz_files(quiz_dir):
        findings, stats = audit_file(
            path,
            baseline=baseline,
            length_margin=args.length_margin,
        )
        all_findings.extend(findings)
        stats_by_file[path.name] = stats

    return print_report(all_findings, stats_by_file)


if __name__ == "__main__":
    sys.exit(main())
