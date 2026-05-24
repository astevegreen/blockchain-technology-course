#!/usr/bin/env python3
"""Verify quiz-bank distractor lengths and longest/shortest distribution targets."""

import argparse
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _target_count(total_questions: int) -> int:
    return round(total_questions * 0.25)


def _classify(corr_len: int, incorr_lens: list[int]) -> dict[str, bool | int]:
    all_lens = [corr_len] + incorr_lens
    max_len = max(all_lens)
    min_len = min(all_lens)

    return {
        "max_len": max_len,
        "min_len": min_len,
        "has_longest_tie": all_lens.count(max_len) > 1,
        "has_shortest_tie": all_lens.count(min_len) > 1,
        "is_longest": corr_len > max(incorr_lens) if incorr_lens else False,
        "is_shortest": corr_len < min(incorr_lens) if incorr_lens else False,
        "is_middle": (
            any(inc_len > corr_len for inc_len in incorr_lens)
            and any(inc_len < corr_len for inc_len in incorr_lens)
        ),
    }


def check_alignment(quiz_dir: Path, margin: float = 0.10) -> int:
    json_files = sorted(quiz_dir.glob("*-quiz-bank.json"))
    if not json_files:
        print(f"Error: No quiz bank JSON files found in {quiz_dir}")
        return 1

    total_questions = 0
    failed_questions = 0
    correct_is_longest = 0
    correct_is_shortest = 0
    correct_is_middle = 0
    uncategorized = 0
    
    total_correct_len = 0
    total_incorrect_len = 0
    incorrect_count = 0
    
    outliers = []
    failed_files = []
    longest_ties = 0
    shortest_ties = 0
    
    print("=== DISTRACTOR LENGTH AND DISTRIBUTION ALIGNMENT REPORT ===")
    print(f"Files analyzed:      {len(json_files)}")
    print(f"Allowed margin:      ±{margin*100:.1f}%\n")
    
    print(f"{'Quiz Bank File':<70} | {'Qs':<3} | {'Long':<4} | {'Short':<5} | {'Mid':<3} | {'Target L/S/M':<12} | {'L/S Ties':<8} | {'Uncat':<5} | {'Status':<6}")
    print("-" * 132)

    for f in json_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error parsing JSON in {f.name}: {e}")
            return 1
            
        questions = data.get("questions", [])
        file_qs = len(questions)
        file_correct_longest = 0
        file_correct_shortest = 0
        file_correct_middle = 0
        file_ties = 0
        file_shortest_ties = 0
        file_margin_failures = 0
        file_uncategorized = 0
        
        for q in questions:
            total_questions += 1
            corr = q.get("correct_answer", "")
            incorr = q.get("incorrect_answers", [])
            
            corr_len = len(corr)
            total_correct_len += corr_len
            
            incorr_lens = [len(x) for x in incorr]
            total_incorrect_len += sum(incorr_lens)
            incorrect_count += len(incorr)
            
            classification = _classify(corr_len, incorr_lens)

            if classification["is_longest"]:
                correct_is_longest += 1
                file_correct_longest += 1
            elif classification["is_shortest"]:
                correct_is_shortest += 1
                file_correct_shortest += 1
            elif classification["is_middle"]:
                correct_is_middle += 1
                file_correct_middle += 1
            else:
                uncategorized += 1
                file_uncategorized += 1

            if classification["has_longest_tie"]:
                longest_ties += 1
                file_ties += 1
            if classification["has_shortest_tie"]:
                shortest_ties += 1
                file_shortest_ties += 1

            # Check if any incorrect answer is outside the margin
            q_failed = False
            for idx, inc_ans in enumerate(incorr):
                inc_len = len(inc_ans)
                dev = abs(inc_len - corr_len) / corr_len if corr_len > 0 else 0
                if dev > margin:
                    q_failed = True
                    file_margin_failures += 1
                    outliers.append({
                        "file": f.name,
                        "question_id": q.get("id"),
                        "correct_answer": corr,
                        "correct_len": corr_len,
                        "incorrect_idx": idx,
                        "incorrect_answer": inc_ans,
                        "incorrect_len": inc_len,
                        "deviation": dev
                    })
            if q_failed:
                failed_questions += 1

        file_longest_target = _target_count(file_qs)
        file_shortest_target = _target_count(file_qs)
        file_middle_target = file_qs - file_longest_target - file_shortest_target
        file_status = "PASS"
        if (
            file_correct_longest != file_longest_target
            or file_correct_shortest != file_shortest_target
            or file_correct_middle != file_middle_target
            or file_ties > 0
            or file_shortest_ties > 0
            or file_uncategorized > 0
            or file_margin_failures > 0
        ):
            file_status = "FAIL"
            failed_files.append(f.name)

        target_summary = f"{file_longest_target}/{file_shortest_target}/{file_middle_target}"
        tie_summary = f"{file_ties}/{file_shortest_ties}"
        print(f"{f.name:<70} | {file_qs:<3} | {file_correct_longest:<4} | {file_correct_shortest:<5} | {file_correct_middle:<3} | {target_summary:<12} | {tie_summary:<8} | {file_uncategorized:<5} | {file_status:<6}")

    print("-" * 132)
    print(f"\nGLOBAL SUMMARY:")
    print(f"Total Questions Analyzed:                         {total_questions}")
    print(f"Questions with ANY distractor violating margin:   {failed_questions} ({failed_questions/total_questions*100:.1f}%)")
    print(f"Questions where correct answer is strictly longest: {correct_is_longest} ({correct_is_longest/total_questions*100:.1f}%)")
    print(f"Questions where correct answer is strictly shortest: {correct_is_shortest} ({correct_is_shortest/total_questions*100:.1f}%)")
    print(f"Questions where correct answer is middle length:    {correct_is_middle} ({correct_is_middle/total_questions*100:.1f}%)")
    print(f"Questions with ties for the longest option:        {longest_ties} ({longest_ties/total_questions*100:.1f}%)")
    print(f"Questions with ties for the shortest option:       {shortest_ties} ({shortest_ties/total_questions*100:.1f}%)")
    print(f"Questions not longest, shortest, or middle:        {uncategorized} ({uncategorized/total_questions*100:.1f}%)")
    
    avg_corr = total_correct_len / total_questions if total_questions > 0 else 0
    avg_incorr = total_incorrect_len / incorrect_count if incorrect_count > 0 else 0
    print(f"Average correct answer length:                     {avg_corr:.1f} chars")
    print(f"Average incorrect answer length:                   {avg_incorr:.1f} chars")
    print(f"Ratio of correct/incorrect:                        {avg_corr/avg_incorr if avg_incorr > 0 else 0:.2f}x")
    
    if outliers:
        print("\n--- OUTLIER SAMPLES (Top 10 largest deviations) ---")
        outliers.sort(key=lambda x: x["deviation"], reverse=True)
        for out in outliers[:10]:
            print(f"\nFile:         {out['file']} (Question: {out['question_id']})")
            print(f"Correct:      [{out['correct_len']} chars] \"{out['correct_answer']}\"")
            print(f"Incorrect #{out['incorrect_idx'] + 1}: [{out['incorrect_len']} chars, +{out['deviation']*100:.1f}% dev] \"{out['incorrect_answer']}\"")
            
    if failed_files:
        print(f"\nFAILURE: The following {len(failed_files)} files failed validation:")
        for name in failed_files:
            print(f"  - {name}")
        return 1
    else:
        print("\nSuccess! All questions have distractors perfectly aligned and compliant with distribution targets!")
        return 0

def main() -> int:
    root = _repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiz-dir",
        type=Path,
        default=root / "quiz_json",
        help="Directory containing *-quiz-bank.json files.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.10,
        help="Allowed length deviation margin as a fraction (e.g. 0.10 for 10%).",
    )
    args = parser.parse_args()
    return check_alignment(args.quiz_dir.resolve(), args.margin)

if __name__ == "__main__":
    sys.exit(main())
