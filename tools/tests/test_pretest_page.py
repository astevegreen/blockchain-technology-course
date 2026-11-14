"""The students' pretest page (blockchain-course/assets/labs/pretest/) and the instructor's marker.

Run: python -m unittest discover -s tools/tests. The page is public, so it must hold no answer; the marker must
read what the page sends, even after a mail program has quoted or wrapped it. The page's own text is made by
pretest.js under node, so the format the page writes and the format the marker reads are tested together.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "blockchain-course" / "assets" / "labs" / "pretest"
sys.path.insert(0, str(REPO / "quizes" / "pretest"))
import build_page  # noqa: E402
import mark_pretest  # noqa: E402

NODE = shutil.which("node")


def page_data() -> dict:
    text = (PAGE / "items.js").read_text(encoding="utf-8")
    return json.loads(text[text.index("=") + 1:].rstrip().rstrip(";"))


def right_option(q: dict) -> str:
    return build_page.option_id(q["id"], q["correct_answer"])


def wrong_option(q: dict) -> str:
    return build_page.option_id(q["id"], q["incorrect_answers"][0])


def page_text(state: dict, week: int | None = None) -> str:
    """What the page would send for `state`, made by pretest.js itself."""
    script = (
        "const P = require(process.argv[1]); const data = require('fs').readFileSync(process.argv[2], 'utf8');"
        "const d = JSON.parse(data.slice(data.indexOf('=') + 1).trim().replace(/;$/, ''));"
        "const s = JSON.parse(process.argv[3]); const w = Number(process.argv[4]) || null;"
        "process.stdout.write(P.answerText(d.form, P.pick(d.items, w), s));")
    out = subprocess.run(["node", "-e", script, str(PAGE / "pretest.js"), str(PAGE / "items.js"),
                          json.dumps(state), str(week or 0)], capture_output=True, check=True)
    return out.stdout.decode("utf-8")


class PageHoldsNoAnswer(unittest.TestCase):
    def test_items_js_is_current_and_clean(self):
        self.assertEqual(build_page.check(), [])

    def test_option_order_says_nothing(self):
        # Options are listed in id order, so the right one is not always first (the banks list it first).
        firsts = 0
        banks = build_page.load_banks()
        by_id = {q["id"]: q for b in banks.values() for q in b["questions"]}
        for item in page_data()["items"]:
            if "options" in item:
                firsts += item["options"][0]["id"] == right_option(by_id[item["id"]])
        self.assertLess(firsts, 20)

    def test_offline(self):
        for path in (PAGE / "index.html", PAGE / "pretest.js"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path.name):
                self.assertIsNone(re.search(r"(?:src|href)\s*=\s*[\"']?(?:https?:)?//", text), "loads from the network")
                self.assertNotIn("type=\"module\"", text)
                self.assertNotIn("fetch(", text)


@unittest.skipUnless(NODE, "node not found")
class RoundTrip(unittest.TestCase):
    def setUp(self):
        self.bank = mark_pretest.load_bank()

    def answers(self, right: bool) -> dict:
        out = {}
        for qid, q in self.bank.items.items():
            if q["question_type"] == "multiple_choice":
                out[qid] = right_option(q) if right else wrong_option(q)
            else:
                out[qid] = "First line of my answer.\nSecond line:\n  indented, with q7: in it"
        return out

    def marked(self, text: str, decisions: dict | None = None) -> dict:
        replies = mark_pretest.parse(text, "reply.txt")
        self.assertEqual(len(replies), 1)
        return mark_pretest.mark(replies, self.bank, decisions or {}, False, [])[replies[0].name]

    def test_all_right_multiple_choice_marks_right(self):
        text = page_text({"name": "Ana Analyst", "answers": self.answers(True)})
        marks = self.marked(text)
        for qid, q in self.bank.items.items():
            with self.subTest(qid):
                self.assertIs(marks[qid], True if q["question_type"] == "multiple_choice" else None)

    def test_written_answer_comes_back_whole(self):
        text = page_text({"name": "Ana Analyst", "answers": self.answers(True)})
        reply = mark_pretest.parse(text)[0]
        self.assertEqual(reply.name, "Ana Analyst")
        self.assertEqual(reply.form, self.bank.form)
        self.assertEqual(reply.answers["q6"], "First line of my answer.\nSecond line:\n  indented, with q7: in it")

    def test_wrong_and_blank(self):
        answers = self.answers(False)
        del answers["q1"], answers["q6"]
        marks = self.marked(page_text({"name": "Bo", "answers": answers}))
        self.assertIs(marks["q1"], False)
        self.assertIs(marks["q2"], False)
        self.assertIs(marks["q6"], False)  # a blank written answer is wrong without asking

    def test_quoted_and_wrapped_reply(self):
        text = page_text({"name": "Cy", "answers": self.answers(True)})
        mangled = []
        for line in text.splitlines():  # a reply quotes every line, and a mail program wraps at 40 characters
            while len(line) > 40:
                mangled.append("> " + line[:40])
                line = line[40:]
            mangled.append("> " + line)
        reply = mark_pretest.parse("Forwarded message\n" + "\n".join(mangled), "fw.txt")[0]
        self.assertEqual(reply.name, "Cy")
        self.assertEqual(" ".join(reply.answers["q6"].split()),
                         "First line of my answer. Second line: indented, with q7: in it")
        marks = mark_pretest.mark([reply], self.bank, {}, False, [])["Cy"]
        self.assertTrue(all(marks[q] for q, i in self.bank.items.items() if i["question_type"] == "multiple_choice"))

    def test_lab_entry(self):
        answers = self.answers(True)
        reply = mark_pretest.parse(page_text({"name": "Di", "answers": answers}))[0]
        decisions = {}
        for qid, q in self.bank.items.items():
            if q["question_type"] == "written":
                key = f"di|{qid}|{mark_pretest.answer_digest(reply.answers[qid])}"
                decisions[key] = qid != "q8"  # q8 (a day-3 gate) judged wrong
        marks = mark_pretest.mark([reply], self.bank, decisions, False, [])["Di"]
        self.assertEqual(mark_pretest.entry(marks, self.bank.gates[1]), "problem")
        self.assertEqual(mark_pretest.entry(marks, self.bank.gates[3]), "worked example")
        undecided = mark_pretest.mark([reply], self.bank, {}, False, [])["Di"]
        self.assertEqual(mark_pretest.entry(undecided, self.bank.gates[1]), "?")
        self.assertEqual(mark_pretest.entry(undecided, self.bank.gates[2]), "problem")  # q45 is multiple choice

    def test_week_one_only(self):
        text = page_text({"name": "Ed", "answers": self.answers(True)}, week=1)
        marks = self.marked(text)
        self.assertNotIn("q18", marks)
        table = mark_pretest.table({"Ed": marks}, self.bank)
        self.assertIn("Day 5", table)
        self.assertNotIn("Day 6", table)

    def test_main_reads_a_folder_of_replies(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "ana.txt").write_text(page_text({"name": "Ana", "answers": self.answers(True)}), encoding="utf-8")
            (folder / "bo.txt").write_text(page_text({"name": "Bo", "answers": {}}), encoding="utf-16")
            out = folder / "results.md"
            self.assertEqual(mark_pretest.main([str(folder), "--no-ask", "--out", str(out)]), 0)
            report = out.read_text(encoding="utf-8")
            self.assertRegex(report, r"\| Ana \| \? ")
            self.assertRegex(report, r"\| Bo \| worked example")

    def test_json_output_for_the_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "ana.txt").write_text(page_text({"name": "Ana", "answers": self.answers(True)}), encoding="utf-8")
            (folder / "bo.txt").write_text(page_text({"name": "Bo", "answers": self.answers(False)}), encoding="utf-8")
            out = folder / "results.json"
            self.assertEqual(mark_pretest.main([str(folder), "--no-ask", "--json", str(out)]), 0)
            data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["form"], self.bank.form)
        ana, bo = data["students"]
        self.assertEqual((ana["name"], bo["name"]), ("Ana", "Bo"))
        self.assertEqual(ana["days"]["2"], "problem")  # q45 is multiple choice, all right
        self.assertEqual(ana["days"]["1"], "unmarked")  # q6 is written and was not judged (--no-ask)
        self.assertEqual(bo["days"]["2"], "worked example")
        self.assertEqual(ana["items"]["q45"], "right")
        self.assertEqual(ana["items"]["q6"], "unmarked")
        self.assertEqual(bo["items"]["q45"], "wrong")
        self.assertEqual(set(ana["days"]), {str(d) for d in range(1, 10)})
        # Written answers travel with the marks so the engine's page can show them beside the model answer.
        written = {q for q, i in self.bank.items.items() if i["question_type"] != "multiple_choice"}
        self.assertEqual(set(ana["written"]), written)
        self.assertEqual(ana["written"]["q6"], "First line of my answer.\nSecond line:\n  indented, with q7: in it")
        self.assertFalse(set(ana["written"]) & {"q45", "q1"})


@unittest.skipUnless(NODE, "node not found")
class PageHelpers(unittest.TestCase):
    def run_js(self, expr: str):
        script = f"const P = require(process.argv[1]); process.stdout.write(JSON.stringify({expr}));"
        out = subprocess.run(["node", "-e", script, str(PAGE / "pretest.js")], capture_output=True, check=True)
        return json.loads(out.stdout)

    def test_fragment(self):
        self.assertEqual(self.run_js("P.readFragment('#to=pat%40agency.gov&week=1')"), {"to": "pat@agency.gov", "week": 1})
        self.assertEqual(self.run_js("P.readFragment('#to=not-an-address&week=9')"), {"to": "", "week": None})

    def test_download_name_keeps_replies_apart(self):
        self.assertEqual(self.run_js("P.fileName('  Ana  O.Neil, Jr ')"), "pretest-answers-ana-o-neil-jr.txt")
        self.assertEqual(self.run_js("P.fileName('')"), "pretest-answers.txt")

    def test_long_answers_do_not_go_in_the_link(self):
        short = self.run_js("P.mailto('pat@agency.gov', 'Pretest answers: Ana', 'q1: abc123')")
        self.assertTrue(short["whole"])
        self.assertIn("q1%3A%20abc123", short["href"])
        long = self.run_js("P.mailto('pat@agency.gov', 'Pretest answers: Ana', 'x'.repeat(3000))")
        self.assertFalse(long["whole"])
        self.assertLessEqual(len(long["href"]), 1800)


if __name__ == "__main__":
    unittest.main()
