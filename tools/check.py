#!/usr/bin/env python3
"""The repo's one check: test what changed, print failures only, exit 0 or 1.

Usage:
  python tools/check.py                 files changed since origin/main (unpushed commits,
                                        staged, unstaged and untracked)
  python tools/check.py --all           everything; rendered HTML only where _site already has it
  python tools/check.py --all --render  render the whole site first (minutes)
  python tools/check.py --stamped       pass at once if this exact tree already passed

On success prints one line: `check: passed (<n> checks, <s>s)`. On failure prints at most
40 lines grouped by check, then `check: FAILED`, and exits 1. Never modifies tracked files;
a green run of changed files leaves a stamp in .git/check-stamps/ for --stamped.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[1]
COURSE = REPO / "blockchain-course"
GLOSSARY_SCRIPTS = COURSE / "glossary" / "scripts"
MINDMAP = COURSE / "assets" / "mindmap.html"
MAX_LINES = 40
SITE_WIDE = (
    "blockchain-course/_quarto.yml",
    "blockchain-course/_extensions/",
    "blockchain-course/scripts/",
    "blockchain-course/templates/",
    "blockchain-course/styles.css",
    "blockchain-course/index.qmd",
)
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
SAFE_PART = re.compile(r"^[A-Za-z0-9._-]+$")
# Git exports these to its hooks; without them every command finds its repository from its own folder,
# so the tool tests' throwaway repositories don't write to this repository's index during a commit.
GIT_HOOK_VARS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR"}
ENV = {k: v for k, v in os.environ.items() if k not in GIT_HOOK_VARS}
ENV |= {"NO_COLOR": "1", "FORCE_COLOR": "0", "PYTHONIOENCODING": "utf-8"}
NOTE = "note: "
STUDENT_TREES = ("blockchain-course/", "dynamic-labs/")  # what students receive (CLAUDE.md rule 1)
PAGES_WORKFLOW = ".github/workflows/pages.yml"
VM_WORKFLOW = ".github/workflows/vm-build.yml"


@dataclass
class Check:
    name: str
    run: Callable[[], list[str]]  # failure lines, plus `note: ` lines that inform without failing


@dataclass
class Plan:
    checks: list[Check] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


def run(cmd: list[str], cwd: Path = REPO, timeout: int = 1800) -> tuple[int, str]:
    """Run a command; return (exit code, stdout+stderr with ANSI codes stripped)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return 127, f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, f"{' '.join(cmd)}: timed out after {timeout}s"
    out = (proc.stdout or b"").decode("utf-8", "replace") + (proc.stderr or b"").decode("utf-8", "replace")
    return proc.returncode, ANSI.sub("", out).replace("\r", "")


def git(root: Path, *args: str) -> str | None:
    """Git's stdout only: its warnings (such as "LF will be replaced by CRLF") go to stderr and are not file names."""
    try:
        proc = subprocess.run(["git", *args], cwd=root, env=ENV, capture_output=True)
    except FileNotFoundError:
        return None
    return proc.stdout.decode("utf-8", "replace").replace("\r", "").strip() if proc.returncode == 0 else None


def changed_files(root: Path = REPO) -> list[str] | None:
    """Files differing from origin/main (or main), plus staged, unstaged and untracked ones.

    Returns None when git cannot tell (not a repo): the caller checks everything.
    """
    if git(root, "rev-parse", "--git-dir") is None:
        return None
    base = next((b for b in ("origin/main", "main") if git(root, "rev-parse", "--verify", "-q", b)), None)
    merge_base = git(root, "merge-base", base, "HEAD") if base else None
    tracked = git(root, "diff", "--name-only", merge_base) if merge_base else git(root, "diff", "--name-only", "HEAD")
    untracked = git(root, "ls-files", "--others", "--exclude-standard")
    names = [*(tracked or "").splitlines(), *(untracked or "").splitlines()]
    return sorted({n.strip() for n in names if n.strip()})


def added_files(root: Path = REPO) -> list[str]:
    """New files only: added since the merge base, or untracked."""
    base = next((b for b in ("origin/main", "main") if git(root, "rev-parse", "--verify", "-q", b)), None)
    merge_base = git(root, "merge-base", base, "HEAD") if base else "HEAD"
    added = git(root, "diff", "--name-only", "--diff-filter=A", merge_base or "HEAD") or ""
    untracked = git(root, "ls-files", "--others", "--exclude-standard") or ""
    return sorted({n for n in [*added.splitlines(), *untracked.splitlines()] if n})


def tracked_files(suffix: str) -> list[str]:
    return [f for f in (git(REPO, "ls-files") or "").splitlines() if f.endswith(suffix)]


def tail(text: str, n: int = 8) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-n:]


# --- individual checks -----------------------------------------------------------------------

def lint_lessons(files: list[str] | None) -> list[str]:
    args = ["--all"] if files is None else files
    code, out = run([sys.executable, str(REPO / "tools" / "qmd_lint.py"), *args])
    return out.splitlines() if code else []


def quarto_warnings(output: str, label: str) -> list[str]:
    """Each WARNING/ERROR block in Quarto output, prefixed with the lesson or step it came from."""
    found, block = [], []
    for line in output.splitlines():
        if re.search(r"\b(WARN(ING)?|ERROR)\b", line):
            if block:
                found.append(" ".join(block))
            block = [line.strip()]
        elif block and line.strip() and line.startswith((" ", "\t")):
            block.append(line.strip())
        elif block:
            found.append(" ".join(block))
            block = []
    if block:
        found.append(" ".join(block))
    return [f"{label}: {w[:300]}" for w in found]


def render_lesson(rel: str) -> list[str]:
    quarto = shutil.which("quarto")
    if not quarto:
        return ["quarto is not on PATH: cannot render lessons"]
    target = Path(rel).relative_to("blockchain-course").as_posix()
    code, out = run([quarto, "render", target], cwd=COURSE, timeout=900)
    problems = quarto_warnings(out, rel)
    if code and not problems:
        problems = [f"{rel}: quarto render exited {code}", *tail(out)]
    return problems


def render_site() -> list[str]:
    quarto = shutil.which("quarto")
    if not quarto:
        return ["quarto is not on PATH: cannot render the site"]
    code, out = run([quarto, "render"], cwd=COURSE, timeout=3600)
    problems = quarto_warnings(out, "site render")
    if code:
        problems = problems or [f"quarto render exited {code}", *tail(out)]
        if "os error 32" in out:
            problems.append("fix: a shell or program has its working directory inside blockchain-course/_site; move it out")
    return problems


def slide_index_check() -> list[str]:
    code, out = run([sys.executable, str(GLOSSARY_SCRIPTS / "build_slide_index.py"), "--check"], cwd=COURSE)
    if code == 0:
        return []
    lines = [line for line in out.splitlines() if line.strip() and not line.startswith("warning:")]
    return lines or tail(out)


def slide_count(text: str) -> int:
    """Slides a lesson shows: headings at or above its slide level, outside divs (hidden or not), code and comments."""
    front = re.match(r"---\n(.*?)\n---\n", text, re.S)
    level = re.search(r"^\s*slide-level:\s*(\d)", front.group(1), re.M) if front else None
    level = int(level.group(1)) if level else 2
    divs = 0  # fenced divs open; a heading inside one starts no slide
    fence, comment, count = "", False, 0
    for line in text[front.end() if front else 0:].splitlines():
        if fence:
            fence = "" if line.startswith(fence) else fence
        elif comment:
            comment = "-->" not in line
        elif line.startswith(("```", "~~~")):
            fence = line[:3]
        elif line.lstrip().startswith("<!--"):
            comment = "-->" not in line
        elif re.match(r":{3,}\s*$", line):
            divs = max(divs - 1, 0)
        elif re.match(r":{3,}\s*\S", line):
            divs += 1
        elif (m := re.match(r"(#{1,6})\s+\S", line)) and len(m.group(1)) <= level and not divs:
            count += 1
    return count


def bib_entries(text: str) -> dict[str, tuple[int, str]]:
    """Each entry's key, mapped to its line number and its text."""
    starts = list(re.finditer(r"^@\w+\s*\{\s*([^,\s]+)\s*,", text, re.M))
    ends = [m.start() for m in starts[1:]] + [len(text)]
    return {m.group(1): (text.count("\n", 0, m.start()) + 1, text[m.start():end]) for m, end in zip(starts, ends)}


def undated_web_sources(text: str, old_keys: set[str]) -> list[tuple[int, str]]:
    """New entries with a `url` and no `urldate`: the "as of" date a web source carries (CLAUDE.md)."""
    return [(line, key) for key, (line, body) in bib_entries(text).items()
            if key not in old_keys and re.search(r"^\s*url\s*=", body, re.M)
            and not re.search(r"^\s*urldate\s*=\s*[{\"]\d{4}-\d{2}-\d{2}[}\"]", body, re.M)]


def bib_dates(rel: str) -> list[str]:
    base = next((b for b in ("origin/main", "main") if git(REPO, "rev-parse", "--verify", "-q", b)), None)
    merge_base = git(REPO, "merge-base", base, "HEAD") if base else None
    old = git(REPO, "show", f"{merge_base}:{rel}") if merge_base else None
    text = (REPO / rel).read_text(encoding="utf-8")
    failures = [f"{rel}:{line}: @{key} has a url but no urldate"
                for line, key in undated_web_sources(text, set(bib_entries(old or "")))]
    if failures:
        failures.append("fix: add `urldate = {YYYY-MM-DD}`, the day the source was read (the /source skill)")
    return failures


def validate_glossary() -> list[str]:
    code, out = run([sys.executable, str(GLOSSARY_SCRIPTS / "validate_glossary.py")], cwd=COURSE)
    if code == 0:
        return []
    return [*out.splitlines()[:20], "fix: edit glossary/lesson_terms/ and rerun the pipeline (blockchain-course/glossary/README.md)"]


def mindmap_links() -> list[str]:
    """Every lessons/...html#/<anchor> link in the mind map must name a rendered section id."""
    if not MINDMAP.exists():
        return [f"{MINDMAP.relative_to(REPO).as_posix()}: missing"]
    text = MINDMAP.read_text(encoding="utf-8")
    links = re.findall(r"(lessons/[\w./-]+?\.html)#/([^\"'\s)<>]+)", text)
    failures, unrendered, ids = [], set(), {}
    for page, anchor in links:
        html = COURSE / "_site" / page
        if not html.exists():
            unrendered.add(page)
            continue
        if page not in ids:
            ids[page] = set(re.findall(r"<section\b[^>]*\bid=\"([^\"]+)\"", html.read_text(encoding="utf-8")))
        if anchor not in ids[page]:
            line = text[: text.find(f"{page}#/{anchor}")].count("\n") + 1
            failures.append(f"blockchain-course/assets/mindmap.html:{line}: #/{anchor} is not a slide in {page}")
    if failures:
        failures.append("fix: a slide heading changed its anchor; point the mind-map link at the new anchor")
    return failures + [f"{NOTE}{page} has never been rendered, so its mind-map links are unchecked"
                       for page in sorted(unrendered)]


def verify_quiz(rel: str) -> list[str]:
    code, out = run([sys.executable, str(REPO / "quizes" / "verify_single_quiz.py"), "--file", str(REPO / rel)])
    if code == 0:
        return []
    keep = [line for line in out.splitlines() if re.search(r"violation|FAIL|Error|error|Target|count:", line)]
    return [f"{rel}: verify_single_quiz.py failed", *[f"  {line.strip()}" for line in (keep or tail(out))[:10]]]


def bundle_quizzes() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="quiz-bundle-check.") as tmp:
        code, out = run([sys.executable, str(REPO / "quizes" / "build_quiz_bank_bundle.py"),
                         "--output", str(Path(tmp) / "bundle.json")])
    if code == 0:
        return []
    errors = [line for line in out.splitlines() if "Error" in line] or tail(out)
    return [f"quiz bundle: {line.strip()}" for line in errors[:5]]


def compile_python(files: list[str]) -> list[str]:
    failures = []
    for rel in files:
        path = REPO / rel
        try:
            compile(path.read_bytes(), rel, "exec")
        except SyntaxError as exc:
            failures.append(f"{rel}:{exc.lineno}: {exc.msg}")
        except (ValueError, OSError) as exc:
            failures.append(f"{rel}: {exc}")
    return failures


def find_bash() -> str | None:
    """Git Bash; never the WSL launcher, which fails on this machine."""
    candidates = [Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"]
    git_exe = shutil.which("git")
    if git_exe:
        git_root = Path(git_exe).resolve().parents[1]
        candidates += [git_root / "bin" / "bash.exe", git_root.parent / "bin" / "bash.exe"]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    found = shutil.which("bash")
    if found and not re.search(r"system32|windowsapps", found, re.IGNORECASE):
        return found
    return None


def syntax_check_shell(files: list[str]) -> list[str]:
    bash = find_bash()
    if not bash:
        return ["bash not found (install Git for Windows): cannot syntax-check shell scripts"]
    failures = []
    for rel in files:
        code, out = run([bash, "-n", rel])
        if code:
            failures += [line.replace("\\", "/") for line in out.splitlines()[:5]] or [f"{rel}: bash -n exited {code}"]
    return failures


def file_names(files: list[str]) -> list[str]:
    bad = [rel for rel in files
           if not all(SAFE_PART.match(part) or part.startswith("@") for part in rel.split("/"))]
    return [f"{rel}: use only letters, digits, '-', '_' and '.' in file and folder names" for rel in bad]


def zip_exclusions(workflow: str) -> list[str]:
    """The `-x "<pattern>"` entries of the src.zip step in pages.yml."""
    return re.findall(r'-x\s+"([^"]+)"', workflow)


def vm_removals(workflow: str) -> list[str]:
    """The paths the "Remove Unused Repo Payload" step of vm-build.yml deletes (`rm` lines, backslash continuations)."""
    step = re.search(r"- name: Remove Unused Repo Payload\n(.*?)(?=\n\s*- name:|\Z)", workflow, re.S)
    removed, deleting = [], False
    for line in (step.group(1) if step else "").splitlines():
        if re.match(r"\s*rm\s+-", line):
            deleting = True
        if deleting:
            removed += [t for t in line.split() if t.startswith("dynamic-labs/")]
            deleting = line.rstrip().endswith("\\")
    return removed


def matches_any(path: str, patterns: list[str], whole_folders: bool) -> bool:
    """zip and shell patterns: `*` crosses `/`; `whole_folders` also counts a folder name for what is inside it."""
    for pattern in patterns:
        pattern = pattern.replace("**", "*")
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if whole_folders and fnmatch.fnmatchcase(path, pattern.rstrip("/") + "/*"):
            return True
    return False


def unfenced_answer_files(tracked: list[str], pages: str, vm: str) -> list[str]:
    """Tracked `*answer*` files under the student trees that src.zip still holds or the VM image still bakes in."""
    zip_x, vm_rm = zip_exclusions(pages), vm_removals(vm)
    problems = []
    for rel in tracked:
        if not rel.startswith(STUDENT_TREES) or "answer" not in Path(rel).name.lower():
            continue
        if not matches_any(rel, zip_x, whole_folders=False):
            problems.append(f'{rel}: ships in src.zip: add -x "{rel}" to the zip step of {PAGES_WORKFLOW}')
        if not matches_any(rel, vm_rm, whole_folders=True):
            problems.append(f"{rel}: baked into the VM: add it to the rm list of {VM_WORKFLOW}")
    return problems


def answer_files() -> list[str]:
    """CLAUDE.md rule 1: an answer key must not reach students through src.zip or the VM image."""
    texts = [(REPO / wf).read_text(encoding="utf-8") if (REPO / wf).is_file() else "" for wf in (PAGES_WORKFLOW, VM_WORKFLOW)]
    return unfenced_answer_files((git(REPO, "ls-files") or "").splitlines(), *texts)


def tool_tests() -> list[str]:
    failures = []
    if (REPO / "tools" / "tests").is_dir():
        code, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tools/tests"], timeout=600)
        if code:
            keep = [line for line in out.splitlines() if re.match(r"^(FAIL|ERROR):|^\w*Error|File \"", line)]
            failures += ["python unit tests failed (python -m unittest discover -s tools/tests)", *(keep or tail(out))[:12]]
    if list((REPO / "tools" / "hooks").glob("*.test.mjs")):
        code, out = run(["node", "--test", "tools/hooks/*.test.mjs"], timeout=600)
        if code:
            keep = [line for line in out.splitlines() if re.match(r"^\s*not ok\b|^\s*error:|^\s*✖", line)]
            failures += ["hook tests failed (node --test tools/hooks/*.test.mjs)", *(keep or tail(out))[:12]]
    return failures


# --- planning ------------------------------------------------------------------------------

def is_lesson(rel: str) -> bool:
    return rel.startswith("blockchain-course/lessons/") and rel.endswith(".qmd") and "/references/" not in rel


def plan_checks(files: list[str] | None, render: bool = False, added: list[str] | None = None) -> Plan:
    """Choose the checks for `files` (None: everything)."""
    plan = Plan()
    everything = files is None
    present = [] if everything else [f for f in files if (REPO / f).is_file()]
    touched = (lambda prefix: True) if everything else (lambda prefix: any(f.startswith(prefix) for f in files))

    lessons = [f for f in present if is_lesson(f)]
    if everything:
        plan.checks.append(Check("lesson lint", lambda: lint_lessons(None)))
    elif lessons:
        plan.checks.append(Check("lesson lint", lambda: lint_lessons(lessons)))

    if everything and render:
        plan.checks.append(Check("site render", render_site))
    elif not everything:
        for rel in lessons:
            plan.checks.append(Check(f"render {Path(rel).name}", lambda rel=rel: render_lesson(rel)))
    for rel in lessons:
        plan.info.append(f"{Path(rel).name}: {slide_count((REPO / rel).read_text(encoding='utf-8'))} slides "
                         "(a lesson fills one 50-minute slot)")

    lessons_changed = everything or any(is_lesson(f) for f in files)
    if lessons_changed or touched("blockchain-course/glossary/"):
        plan.checks.append(Check("glossary slide index", slide_index_check))
    if touched("blockchain-course/glossary/"):
        plan.checks.append(Check("glossary", validate_glossary))
    if lessons_changed or touched("blockchain-course/assets/mindmap.html"):
        plan.checks.append(Check("mind-map links", mindmap_links))

    bibs = sorted(f.relative_to(REPO).as_posix() for f in (COURSE / "lessons" / "references").glob("*.bib"))
    bibs = bibs if everything else [f for f in present if f in bibs]
    if bibs:
        plan.checks.append(Check("bib dates", lambda: [line for b in bibs for line in bib_dates(b)]))

    if not everything and any(f.startswith(SITE_WIDE) for f in files):
        plan.info.append("site-wide change: run `python tools/check.py --all --render` (renders the whole site)")

    banks = sorted((REPO / "quizes" / "quiz_json").glob("*-quiz-bank.json")) if everything else []
    bank_files = ([b.relative_to(REPO).as_posix() for b in banks] if everything
                  else [f for f in present if re.match(r"quizes/quiz_json/[^/]+\.json$", f)])
    if bank_files:
        plan.checks.append(Check("quiz banks", lambda: [line for b in bank_files for line in verify_quiz(b)]))
        plan.checks.append(Check("quiz bundle", bundle_quizzes))

    py = tracked_files(".py") if everything else [f for f in present if f.endswith(".py")]
    if py:
        plan.checks.append(Check("python syntax", lambda: compile_python(py)))
    sh = tracked_files(".sh") if everything else [f for f in present if f.endswith(".sh")]
    if sh:
        plan.checks.append(Check("shell syntax", lambda: syntax_check_shell(sh)))

    new = added if added is not None else ([] if everything else [f for f in files if f in present])
    if new:
        plan.checks.append(Check("file names", lambda: file_names(new)))

    if touched(".github/workflows/") or any("answer" in Path(f).name.lower() for f in files):
        plan.checks.append(Check("answer files", answer_files))

    if touched("tools/") or touched(".claude/"):
        plan.checks.append(Check("tool tests", tool_tests))

    if not everything and touched("dynamic-labs/"):
        plan.info.append("dynamic-labs changed: Docker is unavailable here, so lab behaviour is unverified")
    return plan


def report(results: list[tuple[str, list[str]]], info: list[str], seconds: float) -> tuple[str, int]:
    """Format the outcome under the output contract; return (text, exit code)."""
    notes = [f"{NOTE}{line}" for line in info]
    notes += [line for _, lines in results for line in lines if line.startswith(NOTE)]
    failed = [(name, [line for line in lines if not line.startswith(NOTE)]) for name, lines in results]
    failed = [(name, lines) for name, lines in failed if lines]
    if not failed:
        return "\n".join([*notes, f"check: passed ({len(results)} checks, {seconds:.1f}s)"]), 0
    body: list[str] = []
    for name, lines in failed:
        body.append(f"[{name}]")
        body += [f"  {line}" for line in lines]
    body += notes
    if len(body) > MAX_LINES:
        body = body[: MAX_LINES - 1] + [f"... ({len(body) - MAX_LINES + 1} more lines)"]
    return "\n".join([*body, "check: FAILED"]), 1


def tree_key(root: Path = REPO) -> str | None:
    """Content hash of the working tree (tracked and untracked, ignored files excluded) plus its merge base.

    Built in a copy of the index, so the real index and the working tree are untouched. None when git can't tell.
    """
    git_dir = git(root, "rev-parse", "--absolute-git-dir")
    if not git_dir:
        return None
    base = next((b for b in ("origin/main", "main") if git(root, "rev-parse", "--verify", "-q", b)), None)
    merge_base = (git(root, "merge-base", base, "HEAD") if base else None) or "none"
    with tempfile.TemporaryDirectory(prefix="check-index.") as tmp:
        index = Path(tmp) / "index"
        if (Path(git_dir) / "index").exists():
            shutil.copy2(Path(git_dir) / "index", index)
        env = {**ENV, "GIT_INDEX_FILE": str(index)}
        if subprocess.run(["git", "add", "-A"], cwd=root, env=env, capture_output=True).returncode:
            return None
        tree = subprocess.run(["git", "write-tree"], cwd=root, env=env, capture_output=True)
    if tree.returncode:
        return None
    return f"{tree.stdout.decode().strip()}-{merge_base[:12]}"


def stamp_path(key: str, root: Path = REPO) -> Path:
    return Path(git(root, "rev-parse", "--absolute-git-dir") or root / ".git") / "check-stamps" / key


def write_stamp(key: str, root: Path = REPO, keep: int = 50) -> None:
    """Record that this tree passed; keep only the newest `keep` stamps."""
    path = stamp_path(key, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(time.strftime("%Y-%m-%d %H:%M:%S\n"), encoding="utf-8")
    stamps = sorted(path.parent.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in stamps[keep:]:
        old.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check what changed; print failures only.")
    parser.add_argument("--all", action="store_true", help="check everything, not just changed files")
    parser.add_argument("--render", action="store_true", help="with --all: render the whole site first")
    parser.add_argument("--stamped", action="store_true",
                        help="pass at once when this exact tree already passed (the git pre-commit hook uses it)")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(errors="replace")  # test output can hold characters a cp1252 console can't show
    if args.render and not args.all:
        parser.error("--render needs --all")
    if args.stamped and args.all:
        parser.error("--stamped checks changed files only")

    start = time.monotonic()
    key = None if args.all else tree_key()
    if args.stamped and key and stamp_path(key).exists():
        print("check: passed (this tree already passed)")
        return 0
    files = None if args.all else changed_files()
    plan = plan_checks(files, render=args.render, added=None if files is None else added_files())
    results = [(check.name, check.run()) for check in plan.checks]
    text, code = report(results, plan.info, time.monotonic() - start)
    if code == 0 and key:
        write_stamp(key)
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
