// The sprint guard (docs/sprint.md, "What still stops a task"): each unattended session's hook refuses what its role
// may not do. Exit 2 is a refusal, 0 lets the call through. Ported from YODC's tests, with the course's lab lock.
import { after, describe, test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { runHook } from "./test-helpers.mjs";

const guard = (mode, toolInput, cwd = process.cwd(), tool = "Bash") =>
  runHook("sprint-guard.mjs", { tool_name: tool, tool_input: toolInput, cwd }, { args: [mode] }).status;
const bash = (mode, command, cwd) => guard(mode, { command }, cwd);
const ps = (mode, command, cwd) => guard(mode, { command }, cwd, "PowerShell");
const BOTH = ["--lane", "--integrator"];
const LABS = "C:/Antigravity/bc-lane-labs";
const LESSONS = "C:/Antigravity/bc-lane-lessons";
const RUN_SH = "dynamic-labs/regression-tests/automated/exercises/run.sh";

describe("every unattended mode", () => {
  for (const command of [
    "git commit --no-verify -m x",
    "SKIP_HOOKS=1 git push",
    "git -c core.hooksPath=/dev/null commit -m x",
    "git -C /w push --force origin HEAD:main",
    "git push origin --delete sprint/3",
    "git push origin +HEAD:main",
    "git reset --hard origin/main",
    "git branch -D sprint/3",
    "python tools/check.py && rm -rf blockchain-course/_site",
    "Remove-Item -Recurse -Force C:/Antigravity/bc-lane-lessons",
    "gh auth switch --user someone",
    "gh api repos/x/y -X DELETE",
    "gh workflow run publish.yml",
    "gh label delete sprint-ready",
    "curl https://example.com",
    "Invoke-WebRequest https://example.com",
  ]) {
    test(`refuses ${command}`, () => {
      for (const mode of BOTH) assert.equal(bash(mode, command), 2, `${mode} ${command}`);
    });
  }
});

describe("--lane", () => {
  test("lets build work through", () => {
    for (const command of [
      "cd /w && python tools/check.py",
      "cd /w && py tools/check.py --all",
      "cd /w/blockchain-course && quarto render lessons/bitcoin/02-BF-transactions_and_mining.qmd",
      "git -C /w switch --discard-changes -C sprint/12 origin/main",
      // The implementer's own steps (.claude/agents/implementer.md, "Build").
      'git -C /w stash --include-untracked -m "left by a stopped session"',
      "git -C /w switch -c sprint/12 origin/main",
      "git -C /w rebase --reapply-cherry-picks origin/main",
      "gh issue edit 12 --add-label to-integrate --remove-label in-progress",
      `git worktree add --detach ${LESSONS} origin/main`,
    ]) assert.equal(bash("--lane", command), 0, command);
  });
  test("never pushes or merges", () => {
    assert.equal(bash("--lane", "python tools/check.py && git push"), 2);
    assert.equal(bash("--lane", "git -C /w push origin HEAD:main"), 2);
    assert.equal(bash("--lane", "gh pr merge 4 --squash"), 2);
    assert.equal(bash("--lane", "git push --dry-run origin HEAD:main"), 2);
  });
  test("installs only the locked dependencies", () => {
    assert.equal(bash("--lane", "cd /w && npm ci"), 0);
    assert.equal(bash("--lane", "python -m pip list"), 0);
    for (const command of ["npm install left-pad", "cd /w && npm i -D left-pad", "npm update",
      "pip install requests", "python -m pip install requests", "py -m pip install -U bibtexparser"]) {
      assert.equal(bash("--lane", command), 2, command);
    }
  });
});

describe("lab tests and Docker (the labs lane's worktree only)", () => {
  test("run in the labs worktree", () => {
    for (const command of [
      `wsl -d Ubuntu -- bash ${RUN_SH} --fresh-start`,
      "wsl -d Ubuntu -- docker ps",
      "docker compose -f dynamic-labs/exercises/docker-compose.yml up -d",
      "bash dynamic-labs/lab-manager.sh status",
      "cd dynamic-labs && ./lab-manager.sh status",
      `${LABS}/${RUN_SH}`,
    ]) assert.equal(bash("--lane", command, LABS), 0, command);
    assert.equal(bash("--lane", `cd ${LABS} && wsl -d Ubuntu -- bash ${RUN_SH} --fresh-start`, LESSONS), 0);
    assert.equal(bash("--lane", `wsl -d Ubuntu -- bash /mnt/c/Antigravity/bc-lane-labs/${RUN_SH}`, LESSONS), 0);
  });
  test("are refused anywhere else", () => {
    for (const command of [
      `wsl -d Ubuntu -- bash ${RUN_SH} --fresh-start`,
      `wsl --distribution Ubuntu --user root bash ${RUN_SH}`,
      "wsl -d Ubuntu -e docker ps",
      "wsl -d Ubuntu -- docker ps",
      "docker ps",
      "docker.exe compose up -d",
      "podman ps",
      `./${RUN_SH}`,
      "bash dynamic-labs/lab-manager.sh start",
      "cd dynamic-labs && ./lab-manager.sh start",
      "bash dynamic-labs/hlf/lab.sh up",
      "timeout 1800 bash dynamic-labs/deploy-cloud.sh",
      "& docker ps",
      "Start-Process wsl -ArgumentList '-d','Ubuntu'",
      'wsl -d Ubuntu -- bash -c "docker ps"',
    ]) assert.equal(bash("--lane", command, LESSONS), 2, command);
  });
  test("the integrator never runs them, even in the labs worktree", () => {
    assert.equal(bash("--integrator", "wsl -d Ubuntu -- docker ps", LABS), 2);
    assert.equal(bash("--integrator", `wsl -d Ubuntu -- bash ${RUN_SH}`, LABS), 2);
  });
  test("reading a lab script or searching for Docker is no lab run", () => {
    for (const command of [
      `cat ${RUN_SH}`,
      `grep -n fresh-start ${RUN_SH}`,
      "grep -rn docker dynamic-labs/README.md",
      "python tools/lab_tests.py",
    ]) assert.equal(bash("--lane", command, LESSONS), 0, command);
  });
});

describe("the sprint queue (tools/sprint/queue.mjs)", () => {
  const Q = "node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs";
  test("runs on its own, with quoted arguments", () => {
    for (const mode of BOTH) {
      for (const command of [
        "node tools/sprint/queue.mjs next lessons --taken 12,14",
        `${Q} has-work "Course lane: lessons"`,
        `${Q} move 12 to-integrate --note 'WHAT CHANGED: a; b | c && d\\nSTUDENT-VISIBLE: nothing students see'`,
        `${Q} status --write --also 'stuck: Course lane: labs (no event since 04:11Z)'`,
      ]) assert.equal(bash(mode, command), 0, `${mode} ${command}`);
    }
  });
  test("refuses it chained, piped, redirected or in the background", () => {
    for (const mode of BOTH) {
      for (const command of [
        `${Q} next lessons > next.txt`,
        `${Q} next lessons 2>&1`,
        `${Q} move 12 held < note.txt`,
        `${Q} next lessons && echo done`,
        `${Q} next lessons; ls`,
        `${Q} next lessons | head -1`,
        "cd C:/Antigravity/blockchain-technology-course && node tools/sprint/queue.mjs next lessons",
        `${Q} next lessons &`,
        `${Q} move 12 held --note "$(git log -1)"`,
        `${Q} move 12 held --note "\`whoami\`"`,
        `${Q} next lessons\nls`,
      ]) assert.equal(bash(mode, command), 2, `${mode} ${command}`);
    }
  });
  test("still lets other commands read the script", () => {
    assert.equal(bash("--lane", "cat tools/sprint/queue.mjs | head -20"), 0);
  });
});

describe("commands run through a wrapper", () => {
  for (const command of [
    "find . -name x -exec git push \\;",
    "find . -exec git push origin HEAD:other ';'",
    "find . -execdir git push {} +",
    "find . -ok git push \\;",
    "find . -exec git {} \\;",
    "git ls-files | xargs git push",
    "echo origin | xargs -n 1 git push",
    "echo push | xargs git",
    "echo push | xargs -I X git X",
    'sh -c "git push"',
    "bash -c 'git push origin HEAD:main'",
    'bash -lc "echo hi"',
    'echo "git push" | bash',
    'bash <<< "git push"',
    'pwsh -c "git push"',
    'pwsh -NoProfile -Command "git push"',
    'powershell -Command "git push"',
    'powershell.exe "git push"',
    "pwsh -EncodedCommand ZwBpAHQAIABwAHUAcwBoAA==",
    "cmd /c git push",
    'cmd.exe /c "git push"',
    'eval "git push"',
    'Invoke-Expression "git push"',
    "Start-Process git -ArgumentList push",
    "env git push",
    "env -i FOO=1 git push",
    "command git push",
    "nice -n 5 git push",
    "timeout 60 git push",
    "timeout -s KILL 60 git push",
    "nohup git push",
    "nohup env nice git push",
    "wsl -d Ubuntu -- git push",
    "wsl -e git push",
    "GIT_TRACE=1 git push",
    "/usr/bin/git push",
    "git.exe push",
    "& git push",
    "then git push",
    "(git push)",
    "git -c alias.x='!git push' x",
    "git -c alias.p=push p",
    "git config alias.p push",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0=push git p",
    'git -C /w rebase -x "git push" origin/main',
    'git submodule foreach "git push"',
  ]) {
    test(`refuses ${command}`, () => {
      for (const mode of BOTH) assert.equal(bash(mode, command), 2, `${mode} ${command}`);
    });
  }
  test("lets the integrator push through a wrapper only as itself", () => {
    assert.equal(bash("--integrator", "timeout 600 git -C C:/Antigravity/bc-integrate push origin HEAD:main"), 0);
    assert.equal(bash("--integrator", "env git push origin HEAD:other"), 2);
  });
  test("lets the look-alikes through", () => {
    for (const mode of BOTH) {
      for (const command of [
        'find blockchain-course -name "*.qmd" -newer CLAUDE.md',
        "find . -name push -type f",
        'find blockchain-course -name "*.qmd" -exec grep -l push {} +',
        "git ls-files | xargs grep -n push",
        "git ls-files tools | xargs -0 wc -l",
        "echo tools/check.py | xargs git log --oneline -1 --",
        "env PYTHONIOENCODING=utf-8 python tools/check.py",
        "timeout 600 python tools/check.py --all",
        "nice -n 10 quarto render lessons/bitcoin/02-BF-transactions_and_mining.qmd",
        "command -v git",
        "bash tools/x.sh",
        "pwsh -NoProfile -File tools/x.ps1",
        "Start-Process -WindowStyle Hidden -WorkingDirectory C:/Antigravity/bc-lane-lessons -FilePath quarto.exe -ArgumentList 'render','lessons/x.qmd' -PassThru",
        'git -C /w commit -m "the alias. we push later"',
        "git -C /w stash push -m wip",
        'gh issue comment 12 --body "sh -c is refused"',
      ]) assert.equal(bash(mode, command), 0, `${mode} ${command}`);
    }
  });
});

describe("commands a variable, a cast or split quotes hide", () => {
  // YODC's 04ce6da6 cases, and the course's own: each runs git push or skips hooks without saying so in a word.
  test("refuses them in PowerShell", () => {
    for (const mode of BOTH) {
      for (const command of [
        "$x = git push origin HEAD:other", "$x=git push origin HEAD:other", "$x += git push origin HEAD:other",
        "$env:X = git push origin HEAD:other", "[string]$x = git push origin HEAD:other", "$o.p = git push origin HEAD:other",
        "$x = @(git push origin HEAD:other)", "[void](git push origin HEAD:other)", "[void] (git push origin HEAD:other)",
        "@(git push origin HEAD:other)", '& "git" push origin HEAD:other',
        "& 'C:\\Program Files\\Git\\bin\\git.exe' push origin HEAD:other", "& { git push origin HEAD:other }",
        ". { git push origin HEAD:other }", '$g = "git"; & $g push origin HEAD:main', '& "$g" push origin HEAD:main',
        "& (Get-Command git) push origin HEAD:main", ". $script", "echo hi & git push origin HEAD:other",
        "git pu`sh origin HEAD:other", "git `\npush origin HEAD:other", "$a = 'push'; git @a origin HEAD:main",
      ]) assert.equal(ps(mode, command), 2, `${mode} ${command}`);
    }
  });
  test("refuses them in bash", () => {
    for (const mode of BOTH) {
      for (const command of [
        "g=git; $g push origin HEAD:main", '"$g" push origin HEAD:main', "${g} push origin HEAD:main",
        'x="git push origin HEAD:main"; $x', 'X="a b" git push origin HEAD:other', 'git "pu"sh origin HEAD:other',
        "git pu''sh origin HEAD:other", "g\\it push origin HEAD:other", "git \\\npush origin HEAD:other",
        "echo hi & git push origin HEAD:other", "p=push; git $p origin HEAD:main", "git $(echo push) origin HEAD:main",
        "git `echo push` origin HEAD:main", "$(which git) push origin HEAD:main", "`which git` push origin HEAD:main",
        '"$(which git)" push origin HEAD:main', 'echo hi; "`which git`" push origin HEAD:main',
        'git -C "$d" commit -m x', 'git commit --no-ver""ify -m x',
      ]) assert.equal(bash(mode, command), 2, `${mode} ${command}`);
    }
  });
  test("lets plain values, saved output and backgrounding through", () => {
    for (const command of ["$x = git status", "& git status", "$LASTEXITCODE",
      "$files | Where-Object { $_.Length -gt 0 } | Select-Object -First 3", "$r = Get-Content x.txt; $r.Count",
      ". ./tools/x.ps1"]) assert.equal(ps("--lane", command), 0, command);
    for (const command of ["npm test > out.txt 2>&1 &", "ls . $HOME", 'x=$(git status) && echo "$x"',
      'gh issue comment 12 --body "Fixed (\\`02-BF\\`); \\`check.py\\` passes & costs \\$0"']) {
      assert.equal(bash("--lane", command), 0, command);
    }
    assert.equal(ps("--integrator", "$out = git -C C:/Antigravity/bc-integrate push origin HEAD:main"), 0);
  });
  test("reads |, ; and & in double quotes holding $ as text outside a $(…) or backticks (YODC 6d5eeed2)", () => {
    for (const command of ['gh issue comment 5 --body "Done; $n left"',
      'gh issue comment 5 --body "$n of 5 | next & X3"', 'gh issue comment 5 --body "Fixed (see $x); next"']) {
      assert.equal(bash("--lane", command), 0, command);
      assert.equal(ps("--lane", command), 0, command);
    }
    for (const mode of BOTH) {
      for (const command of ['gh issue comment 5 --body "a; $(echo hi; git push)"', 'echo "a; `echo hi; git push`"',
        'echo "$n; $((1 + 2)); $( (cd x); git push --force)"']) {
        assert.equal(bash(mode, command), 2, `${mode} ${command}`);
      }
      assert.equal(ps(mode, 'gh issue comment 5 --body "a; $(echo hi; git push)"'), 2, mode);
    }
  });
});

describe("--integrator", () => {
  test("pushes only HEAD to main", () => {
    assert.equal(bash("--integrator", "git -C C:/Antigravity/bc-integrate push origin HEAD:main"), 0);
    assert.equal(bash("--integrator", "git push origin HEAD:refs/heads/other"), 2);
    assert.equal(bash("--integrator", "git push"), 2);
  });
  test("reads a push that saves its output to a file as that push", () => {
    assert.equal(bash("--integrator", "git -C C:/Antigravity/bc-integrate push origin HEAD:main > push.txt 2>&1"), 0);
    assert.equal(bash("--integrator", "git -C C:/Antigravity/bc-integrate push origin HEAD:main --force > x"), 2);
    assert.equal(bash("--integrator", "git push origin HEAD:other > x"), 2);
  });
});

describe("--read-only", () => {
  test("runs inspection commands only", () => {
    assert.equal(bash("--read-only", "git diff origin/main...sprint/3 | head -50"), 0);
    assert.equal(bash("--read-only", "git show sprint/3:blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd"), 0);
    assert.equal(bash("--read-only", "gh issue view 3 --comments"), 0);
    assert.equal(bash("--read-only", "python tools/check.py"), 2);
    assert.equal(bash("--read-only", "quarto render lessons/x.qmd"), 2);
    assert.equal(bash("--read-only", "git diff > out.txt"), 2);
    assert.equal(bash("--read-only", "git log && git commit -m x"), 2);
  });
  test("reads slide counts and titles from a revision with check.py --slides", () => {
    assert.equal(bash("--read-only", "python tools/check.py --slides blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd --at sprint/3"), 0);
    assert.equal(bash("--read-only", "py C:/Antigravity/blockchain-technology-course/tools/check.py --slides x.qmd --at sprint/3"), 0);
    assert.equal(bash("--read-only", "python tools/check.py --all"), 2);
    assert.equal(bash("--read-only", "python tools/check.py --slides x.qmd > out.txt"), 2);
  });
  test("reads quoted `>` as text and allows cd", () => {
    assert.equal(bash("--read-only", 'cd /w && grep -n "a > b" tools/check.py'), 0);
    assert.equal(bash("--read-only", "git log --format='%h > %s'"), 0);
    assert.equal(bash("--read-only", "cd /w && git diff >> out.txt"), 2);
  });
  test("reads |, ; and & inside quotes as a search pattern, but still splits command substitutions", () => {
    assert.equal(bash("--read-only", 'grep -n "peel\\|change" blockchain-course/lessons'), 0);
    assert.equal(bash("--read-only", 'grep -n "a\\|b;c" blockchain-course'), 0);
    assert.equal(bash("--read-only", "grep -rn 'x|y' blockchain-course"), 0);
    assert.equal(bash("--read-only", 'grep "a" x; git commit -m x'), 2);
    assert.equal(bash("--lane", 'echo "$(git push)"'), 2);
    assert.equal(bash("--lane", 'echo "`git push`"'), 2);
    assert.equal(bash("--lane", 'echo \\"x; git push; y\\"'), 2);
    assert.equal(bash("--lane", 'grep "a|b" x | git push'), 2);
  });
  test("reads backticks and $ inside single quotes as text, as bash does (the 24 Oct review)", () => {
    const Q = "node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs";
    for (const command of [
      `${Q} move 12 to-integrate --note 'WHAT CHANGED: reworks \`ethereum/01-EF-ethereum_intro.qmd\`\\nSTUDENT-VISIBLE: x'`,
      `${Q} status --write --also 'session \`Course lane: labs\` stuck, cost $(none)'`,
      "gh issue create --title 'X4: Explorer' --body '**Check**: the lab run proves it; Run `docker ps` first.'",
      "gh issue create --title 'X1' --body 'Run `python tools/check.py`; which `run.sh --fresh-start` proves it'",
    ]) assert.equal(bash("--lane", command, LESSONS), 0, command);
    assert.equal(bash("--integrator", "gh issue comment 12 --body 'Integrator: rebase with `git rebase --reapply-cherry-picks origin/main`'"), 0);
    // In double quotes the backticks run: this comment would rebase the main checkout. A stand-in main checkout
    // (a `.git` folder), so the answer is the same when the tests run in a worktree.
    const main = mkdtempSync(path.join(os.tmpdir(), "bc-sprint-guard-main-"));
    mkdirSync(path.join(main, ".git"));
    try {
      assert.equal(bash("--integrator", 'gh issue comment 12 --body "Integrator: rebase with `git rebase --reapply-cherry-picks origin/main`"', main), 2);
    } finally {
      rmSync(main, { recursive: true, force: true });
    }
    assert.equal(bash("--lane", "echo 'x' `git push`"), 2);
  });
  test("lets a note or comment name curl or a recursive delete, but runs neither", () => {
    const Q = "node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs";
    for (const command of [
      `${Q} move 12 to-integrate --note 'WHAT CHANGED: step 3 uses curl against the node RPC'`,
      "gh issue comment 12 --body 'Implementer: lab tests\nPASS curl rpc\nPASS rm -rf of the old volume'",
    ]) assert.equal(bash("--lane", command, LESSONS), 0, command);
    assert.equal(bash("--read-only", 'git show sprint/12:x.qmd | grep -n "curl"'), 0);
    for (const command of ["`curl x`", "'curl' x", "env 'curl' x", "\"curl\" x", "Start-Process 'curl' -ArgumentList x",
      "$r = iwr x", "rm -rf \"$HOME\"", "'rm' -rf x", 'echo "$(curl x)"']) {
      for (const mode of BOTH) assert.equal(bash(mode, command), 2, `${mode} ${command}`);
    }
  });
  test("lets a message name a force-push or --no-verify; a quoted argument or a value that runs is still read", () => {
    const Q = "node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs";
    for (const command of [
      "gh issue comment 5 --body 'see $(git push --force origin main)'",
      `${Q} move 12 held --note 'refused: git push --force is never allowed'`,
      "git -C /w commit -m 'Explain why the hook refuses --no-verify'",
      `${Q} status --write --also 'the guard stopped git reset --hard'`,
      'gh issue comment 5 --body="the owner restores with git reset --hard"',
    ]) for (const mode of BOTH) assert.equal(bash(mode, command, LESSONS), 0, `${mode} ${command}`);
    for (const command of [
      'gh issue comment 5 --body "see `git push --force origin main`"',
      'gh issue comment 5 --body "$(git push --force origin main)"',
      `${Q} move 5 to-integrate --note "done $(git push origin HEAD:main)"`,
      'gh issue comment 5 --body "$(curl -s https://example.com)"',
      "echo $(git push --force origin main)",
      "git push '--force' origin HEAD:main",
      "git commit '--no-verify' -m x",
      "echo 'git push --force' && git push --force",
    ]) for (const mode of BOTH) assert.equal(bash(mode, command, LESSONS), 2, `${mode} ${command}`);
  });
  test("reads git config but never writes it", () => {
    for (const command of ["git config user.name", "git config --get user.email", "git config --list",
      "git config get core.autocrlf", "git -C /w config --show-origin --get-all remote.origin.url"]) {
      for (const mode of BOTH) assert.equal(bash(mode, command, LESSONS), 0, `${mode} ${command}`);
    }
    for (const command of ["git config user.name x", "git config --global user.name x", "git config set core.x y",
      "git config --unset core.x", "git -C /w config --local merge.bib.driver x", "git config --edit",
      "git config --worktree core.sparseCheckout true"]) {
      for (const mode of BOTH) assert.equal(bash(mode, command, LESSONS), 2, `${mode} ${command}`);
    }
  });
  test("reads a PowerShell assignment as the command it saves", () => {
    for (const command of ["$x = git push", "$x=git push", "$x = (git push", "[string]$x += git push", "$env:X = git push",
      "$null = git -C /w push origin HEAD:main"]) assert.equal(ps("--lane", command), 2, command);
    assert.equal(ps("--integrator", "$r = git -C C:/Antigravity/bc-integrate push origin HEAD:main"), 0);
    assert.equal(ps("--integrator", "$r = git push origin HEAD:other"), 2);
    assert.equal(ps("--lane", "$r = gh issue view 12 --json labels"), 0);
  });
  test("reads a backslash-escaped ; or | outside quotes as text, as bash does", () => {
    // YODC's 22 Oct eval: this refusal hid a bug from the reviewer.
    assert.equal(bash("--read-only", "sed -n 190,210p\\;350,490p blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd"), 0);
    assert.equal(bash("--read-only", "grep -n peel\\|change blockchain-course"), 0);
    // cat is handed the words `;`, `git` and `commit` to read: nothing runs git.
    assert.equal(bash("--read-only", "cat x \\; git commit -m y"), 0);
  });
  test("still splits at an unescaped operator next to an escaped one", () => {
    assert.equal(bash("--read-only", "sed -n 1p\\; x; git commit -m y"), 2);
    assert.equal(bash("--read-only", "sed -n 1p\\;2p x && git commit -m y"), 2);
    assert.equal(bash("--read-only", "sed -n 1p\\;2p x | git commit -m y"), 2);
    // `\\` is an escaped backslash, so the `;` after it ends the command.
    assert.equal(bash("--lane", "grep a x \\\\; git push"), 2);
    assert.equal(bash("--lane", "echo \\$(git push)"), 2);
  });
  test("reads a backslash-newline as one command line", () => {
    assert.equal(bash("--lane", "git \\\npush origin HEAD:main"), 2);
    assert.equal(bash("--read-only", "git log \\\n  --oneline -3"), 0);
  });
  test("fetches origin and reads with --no-pager", () => {
    assert.equal(bash("--read-only", "git fetch -q origin"), 0);
    assert.equal(bash("--read-only", "git --no-pager log -3"), 0);
    assert.equal(bash("--read-only", "git fetch origin main:main"), 2);
    assert.equal(bash("--read-only", "git push"), 2);
  });
});

describe("--github", () => {
  const plugin = (name) => guard("--github", {}, process.cwd(), `mcp__plugin_github_github__${name}`);
  test("refuses the GitHub plugin's writes, which sign in as the owner", () => {
    for (const name of ["add_issue_comment", "issue_write", "update_issue_comment", "create_pull_request", "push_files",
      "merge_pull_request", "sub_issue_write", "pull_request_review_write", "create_or_update_file", "delete_file"]) {
      assert.equal(plugin(name), 2, name);
    }
  });
  test("lets its reads through", () => {
    for (const name of ["issue_read", "pull_request_read", "get_me", "list_issues", "search_issues"]) assert.equal(plugin(name), 0, name);
  });
});

// Owner, 28 Oct 2026: "Web and Notion read". A trigger names the connector "Notion"; this desktop names it by id.
describe("--notion", () => {
  const notion = (name, server = "Notion") => guard("--notion", {}, process.cwd(), `mcp__${server}__${name}`);
  test("lets the reads through, under either name", () => {
    for (const name of ["notion-fetch", "notion-search", "notion-get-comments", "notion-list-page-backlinks",
      "notion-query-data-sources", "notion-memory-search"]) {
      assert.equal(notion(name), 0, name);
      assert.equal(notion(name, "87a483d9-4e5a-43ab-9e93-d5787ad4a8b0"), 0, name);
    }
  });
  test("refuses every write", () => {
    for (const name of ["notion-create-pages", "notion-update-page", "notion-create-comment", "notion-move-pages",
      "notion-delete-pages", "notion-duplicate-page", "notion-update-data-source", "notion-create-file-upload",
      "notion-spawn-session", "notion-set-discussion-resolved"]) assert.equal(notion(name), 2, name);
  });
});

describe("--file-lock", () => {
  const tmp = mkdtempSync(path.join(os.tmpdir(), "bc-sprint-guard-"));
  const main = path.join(tmp, "blockchain-technology-course");
  const lane = path.join(tmp, "bc-lane-lessons");
  mkdirSync(path.join(main, ".git"), { recursive: true });
  mkdirSync(lane, { recursive: true });
  writeFileSync(path.join(lane, ".git"), "gitdir: elsewhere\n");
  after(() => rmSync(tmp, { recursive: true, force: true }));
  // Bash reads a backslash as an escape, so a command names these folders with forward slashes, as the skills do.
  const [mainSh, laneSh] = [main, lane].map((p) => p.split(path.sep).join("/"));
  const edit = (file) => guard("--file-lock", { file_path: file }, lane);

  test("lets a lane edit its own worktree", () => {
    for (const rel of ["blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd",
      "blockchain-course/lessons/references/Blockchain.bib", "blockchain-course/glossary/lesson_terms/01-BF-bitcoin_origins_and_mechanics.yml",
      "dynamic-labs/exercises/l03-i3-trust-game/README.md", "quizes/quiz_json/x-quiz-bank.json", "docs/build-spec.md"]) {
      assert.equal(edit(path.join(lane, rel)), 0, rel);
    }
  });
  test("keeps git writes out of the main checkout", () => {
    for (const mode of BOTH) {
      assert.equal(bash(mode, "git switch -C sprint/3 origin/main", main), 2);
      assert.equal(bash(mode, `git -C ${mainSh} cherry-pick abc..def`, lane), 2);
      assert.equal(bash(mode, `cd ${mainSh} && git commit -m x`, lane), 2);
      assert.equal(bash(mode, "git stash", main), 2);
      assert.equal(bash(mode, "git fetch origin --prune && git merge --ff-only origin/main", main), 0);
      assert.equal(bash(mode, `git -C ${laneSh} switch --discard-changes -C sprint/3 origin/main`, main), 0);
      assert.equal(bash(mode, "git commit -m x", lane), 0);
      assert.equal(bash(mode, `git -C ${laneSh} stash push -m left`, main), 0);
      assert.equal(bash(mode, `git -C ${mainSh} stash push -m x`, lane), 2);
      // Through a wrapper, and past a `-c` setting before the subcommand.
      assert.equal(bash(mode, `env git -C ${mainSh} commit -m x`, lane), 2);
      assert.equal(bash(mode, `git -c user.name=x -C ${mainSh} commit -m x`, lane), 2);
      assert.equal(bash(mode, `find ${mainSh} -maxdepth 0 -exec git -C {} commit -m x \\;`, lane), 2);
      // A backslash path stays whole in double quotes in bash, and anywhere in PowerShell.
      assert.equal(bash(mode, `git -C "${main}" commit -m x`, lane), 2);
      assert.equal(ps(mode, `git -C ${main} commit -m x`, lane), 2);
      assert.equal(ps(mode, `git -C ${lane} commit -m x`, main), 0);
    }
  });
  test("refuses the main checkout, the sprint's machinery, the owner's files and generated files", () => {
    assert.equal(edit(path.join(main, "blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd")), 2);
    for (const locked of [".claude/agents/implementer.md", ".claude/settings.json", "docs/sprint.md", "CLAUDE.md",
      ".githooks/pre-commit", ".github/workflows/pages.yml", ".gitattributes", "tools/sprint/rules.mjs",
      "tools/hooks/sprint-guard.mjs", "tools/check.py", "blockchain-course/glossary/terms.yml",
      "blockchain-course/glossary/slide-index.yml", "blockchain-course/glossary/index.qmd", "quizes/dist/bundle.json",
      "blockchain-course/_site/index.html"]) {
      assert.equal(edit(path.join(lane, locked)), 2, locked);
    }
  });
  test("refuses a file outside every checkout", () => {
    assert.equal(edit(path.join(os.tmpdir(), "bc-no-checkout", "x.txt")), 2);
  });
});
