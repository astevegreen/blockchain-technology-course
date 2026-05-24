#!/usr/bin/env python3
"""Verify a single quiz bank against distractor length-distribution rules."""

import argparse
import json
import sys
from pathlib import Path


def _target_count(total_questions: int) -> int:
    """Return the per-bank target for longest-correct and shortest-correct items."""
    return round(total_questions * 0.25)


def _classify(corr_len: int, incorr_lens: list[int]) -> dict[str, bool | int]:
    all_lens = [corr_len] + incorr_lens
    max_len = max(all_lens)
    min_len = min(all_lens)

    has_longest_tie = all_lens.count(max_len) > 1
    has_shortest_tie = all_lens.count(min_len) > 1
    is_longest = corr_len > max(incorr_lens) if incorr_lens else False
    is_shortest = corr_len < min(incorr_lens) if incorr_lens else False
    is_middle = (
        any(inc_len > corr_len for inc_len in incorr_lens)
        and any(inc_len < corr_len for inc_len in incorr_lens)
    )

    return {
        "max_len": max_len,
        "min_len": min_len,
        "has_longest_tie": has_longest_tie,
        "has_shortest_tie": has_shortest_tie,
        "is_longest": is_longest,
        "is_shortest": is_shortest,
        "is_middle": is_middle,
    }


def check_single_quiz(file_path: Path, margin: float = 0.10) -> int:
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist.")
        return 2

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error parsing JSON in {file_path.name}: {e}")
        return 2

    questions = data.get("questions", [])
    total_questions = len(questions)
    if total_questions == 0:
        print(f"Error: No questions found in {file_path.name}")
        return 2

    # Target: 25% longest-correct, 25% shortest-correct, remaining middle.
    # 13 questions -> 3 longest, 3 shortest, 7 middle.
    # 16 questions -> 4 longest, 4 shortest, 8 middle.
    target_longest = _target_count(total_questions)
    target_shortest = _target_count(total_questions)
    target_middle = total_questions - target_longest - target_shortest
    
    correct_is_longest_count = 0
    correct_is_shortest_count = 0
    correct_is_middle_count = 0
    uncategorized_count = 0
    margin_violations = 0
    longest_ties = 0
    shortest_ties = 0
    
    print(f"=== Single Quiz Length Verification: {file_path.name} ===")
    print(f"Total questions: {total_questions}")
    print(f"Target 'correct is strictly longest' count: {target_longest}")
    print(f"Target 'correct is strictly shortest' count: {target_shortest}")
    print(f"Target 'correct is middle length' count: {target_middle}")
    
    for q in questions:
        q_id = q.get("id", "unknown")
        corr = q.get("correct_answer", "")
        incorr = q.get("incorrect_answers", [])
        
        corr_len = len(corr)
        incorr_lens = [len(x) for x in incorr]
        
        # Check margin violations
        for idx, inc_ans in enumerate(incorr):
            inc_len = len(inc_ans)
            dev = abs(inc_len - corr_len) / corr_len if corr_len > 0 else 0
            if dev > margin:
                print(f"  [MARGIN VIOLATION] Q {q_id}: Incorrect #{idx+1} len {inc_len} vs Correct len {corr_len} ({dev*100:.1f}% dev, allowed {margin*100:.1f}%)")
                margin_violations += 1
                
        classification = _classify(corr_len, incorr_lens)

        if classification["is_longest"]:
            correct_is_longest_count += 1
        elif classification["is_shortest"]:
            correct_is_shortest_count += 1
        elif classification["is_middle"]:
            correct_is_middle_count += 1
        else:
            print(f"  [CATEGORY VIOLATION] Q {q_id}: Correct length is neither strictly longest, strictly shortest, nor middle (Lengths: Correct={corr_len}, Incorrects={incorr_lens})")
            uncategorized_count += 1

        if classification["has_longest_tie"]:
            max_occurrences = ([corr_len] + incorr_lens).count(classification["max_len"])
            print(f"  [LONGEST TIE] Q {q_id}: Longest option length {classification['max_len']} is shared by {max_occurrences} options (Lengths: Correct={corr_len}, Incorrects={incorr_lens})")
            longest_ties += 1

        if classification["has_shortest_tie"]:
            min_occurrences = ([corr_len] + incorr_lens).count(classification["min_len"])
            print(f"  [SHORTEST TIE] Q {q_id}: Shortest option length {classification['min_len']} is shared by {min_occurrences} options (Lengths: Correct={corr_len}, Incorrects={incorr_lens})")
            shortest_ties += 1
        
    print(f"\nResults:")
    print(f"- 'Correct is strictly longest' count: {correct_is_longest_count} / {total_questions} (Target: {target_longest})")
    print(f"- 'Correct is strictly shortest' count: {correct_is_shortest_count} / {total_questions} (Target: {target_shortest})")
    print(f"- 'Correct is middle length' count: {correct_is_middle_count} / {total_questions} (Target: {target_middle})")
    print(f"- Margin violations: {margin_violations}")
    print(f"- Longest option ties: {longest_ties}")
    print(f"- Shortest option ties: {shortest_ties}")
    print(f"- Uncategorized length positions: {uncategorized_count}")
    
    success = True
    if correct_is_longest_count != target_longest:
        print(f"FAIL: 'Correct is strictly longest' count ({correct_is_longest_count}) does not match target ({target_longest}).")
        success = False
    if correct_is_shortest_count != target_shortest:
        print(f"FAIL: 'Correct is strictly shortest' count ({correct_is_shortest_count}) does not match target ({target_shortest}).")
        success = False
    if correct_is_middle_count != target_middle:
        print(f"FAIL: 'Correct is middle length' count ({correct_is_middle_count}) does not match target ({target_middle}).")
        success = False
    if margin_violations > 0:
        print(f"FAIL: Has {margin_violations} margin violation(s).")
        success = False
    if longest_ties > 0:
        print(f"FAIL: Has {longest_ties} tie(s) for the longest option.")
        success = False
    if shortest_ties > 0:
        print(f"FAIL: Has {shortest_ties} tie(s) for the shortest option.")
        success = False
    if uncategorized_count > 0:
        print(f"FAIL: Has {uncategorized_count} question(s) where the correct answer is not longest, shortest, or middle.")
        success = False
        
    if success:
        print("SUCCESS! File is compliant with all distractor length requirements.")
        return 0
    else:
        print("FAILURE! File violates one or more requirements.")
        return 1

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the quiz bank JSON file.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.10,
        help="Allowed length deviation margin as a fraction (default: 0.10).",
    )
    args = parser.parse_args()
    return check_single_quiz(args.file.resolve(), args.margin)

if __name__ == "__main__":
    sys.exit(main())
