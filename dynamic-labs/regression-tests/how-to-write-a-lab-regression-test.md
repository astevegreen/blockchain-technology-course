# How To Write a Lab Regression Test

## Purpose

This document defines the standard for adding regression coverage to a
single lab in `dynamic-labs`.

The standard is generic, but every regression suite must stay scoped to
one lab. A lab may depend on shared platform services such as the router,
shared auth, and lane-service, but the suite must still answer one
question clearly:

"Does this specific lab work correctly from a fresh deployment?"

## Core Rules

1. Write regression coverage per lab, not as one giant cross-lab suite.
2. Maximize non-browser automation first. Use browser-driven MCP checks
   only after code-driven coverage is in place.
3. Support two entry modes:
   - default non-destructive mode that reuses the current environment
   - optional fresh-start mode that wipes runtime state and recreates the
     lab from scratch
4. Preserve built Docker images so the test run does not have to rebuild
   everything, but treat containers, volumes, claims, cookies, runtime
   files, and generated state as disposable.
5. Full fresh-start coverage is still required somewhere in the suite,
   but it is not the default way to begin every run.
6. Use real services, real routes, and real containers. Do not mock the
   router, lane-service, ttyd, or the lab's backing services for
   regression tests.
7. Prefer Python `requests` over ad hoc `curl` for repeatable HTTP
   assertions.
8. If a page tells the student to run a command, that command should be
   validated against the real lab environment.
9. Command verification and ttyd verification are separate requirements:
   command correctness may be checked with `exec`, but ttyd must still be
   tested at least once through the real web path.

## Directory Layout

All new regression assets live under `regression-tests/`.

```text
regression-tests/
  automated/
    <lab>/
      ...
  agent/
    <lab>/
      playbook.md
      suite.yaml
      tasks/
        *.md
```

Rules for the layout:

- `automated/<lab>/` contains code-driven tests.
- `agent/<lab>/` contains reusable human-or-agent playbooks.
- `agent/<lab>/suite.yaml` should define the task list when the browser
  stage is meant to be split across multiple agents or contexts.
- `agent/<lab>/tasks/*.md` should hold the individual task instructions
  referenced by the suite manifest.
- Each lab gets its own directory under both trees.
- Shared platform surfaces that are not owned by one lab may use a
  narrow dedicated directory such as `agent/portal/`.
- Shared helpers are allowed, but test cases and playbooks should still
  resolve to one owning lab or one explicit shared platform surface.

## Entry Modes

Every lab suite must define both:

1. a default non-destructive entry path
2. an optional fresh-start reset path

### Default Non-Destructive Mode

This is the default way to begin a regression run.

Purpose:

- validate behavior without disrupting other active work
- reuse the currently running environment when it is trustworthy
- avoid unnecessary teardown of unrelated services

The normal pattern is:

1. verify the existing environment is usable
2. run the automated stage
3. run the agent stage against the same live environment

### Optional Fresh-Start Mode

This mode is used when we explicitly want deployment-from-scratch
coverage.

Fresh-start mode means wiping the lab back to a fresh-start state before
testing.

Use fresh-start mode when:

- validating first-deploy behavior
- explicitly verifying reset idempotence
- recovering from a failed or contaminated run
- preparing a high-confidence release gate

The fresh-start reset is not a requirement before every individual test
or every stage. If a run begins in fresh-start mode, the normal pattern
is:

1. reset once
2. boot once
3. run the automated stage
4. run the agent stage against the same live environment

For this standard, a fresh-start reset means:

1. Stop all managed services relevant to the lab.
2. Remove disposable containers.
3. Remove named volumes used by the lab and its supporting services.
4. Remove lane-service runtime state and any persisted claim/session
   state relevant to the lab.
5. Remove generated runtime files that would not exist on a brand-new VM
   deployment, unless the specific test is intentionally validating
   restart behavior instead of first deployment behavior.
6. Preserve built Docker images so the stack can be recreated without a
   full rebuild.

Important:

- Preserving container writable state is not allowed. That breaks the
  fresh-start guarantee.
- A lab suite should document how to decide whether the current live
  environment is trustworthy enough for non-destructive mode.
- A lab suite should be able to run twice in a row and produce the same
  result after the reset step when fresh-start mode is used.

## Required Layers

Every lab regression effort should cover these layers in order.

### 1. Reset and Deployment Smoke

Prove that the lab can be wiped and stood back up from scratch when
fresh-start mode is requested.

Minimum checks:

- shared infrastructure comes up
- lab-specific services come up
- health or status surfaces respond
- required networks exist
- the lab is reachable through the shared router

### 2. Router and HTTP Contract

Prove that the user-facing routes behave correctly.

Minimum checks:

- expected redirects
- expected status codes
- expected cookies
- expected protected routes for instructor surfaces
- expected shared surfaces such as landing pages, wrappers, APIs, or
  supplemental tools

### 3. Service Integration

Prove that the lab's internal services work together.

Examples:

- lane claim and lane resolution
- shared auth and instructor gating
- mempool or explorer reachability
- RPC or API calls
- persisted data initialization

For integration-style checks, the default pattern is a dedicated test
runner container attached to `router-net`.

### 4. Command Verification

Prove that commands students are told to run actually work.

Rules:

- Use the real lab container environment.
- It is acceptable to use container `exec` for command verification.
- Do not replace the commands with mocks or static expected output.
- Assertions should check meaningful outcomes, not just exit code `0`.

### 5. TTYD Verification

Prove that the terminal is usable through the real web path.

Rules:

- This is a separate requirement from command verification.
- At least one test path must exercise ttyd through the browser-facing
  route.
- Input must be sent the same way a student would send it through ttyd.
- If ttyd is validated in the agent playbook instead of the automated
  suite, the automated suite should say so explicitly.

### 6. Instructor Surface Verification

If the lab has instructor-only routes, test them.

Minimum checks:

- unauthenticated access is rejected or redirected correctly
- authenticated access succeeds
- the instructor-specific surface actually loads and is functional

### 7. Reset Idempotence

The suite should prove that the reset step really works.

Minimum checks:

- run reset
- boot lab
- exercise the lab
- run reset again
- boot lab again
- confirm no stale state leaked into the second run

This does not mean every stage should perform its own reset. It means
the overall suite should include at least one explicit proof that a
second clean run behaves like the first.

## Automated Test Standard

Automated tests are the default first layer.

Preferred order:

1. unit or service-local tests when they meaningfully protect behavior
2. HTTP and integration tests through the shared router
3. container command verification
4. optional protocol-level ttyd checks if they can be done reliably
   without browser MCP

Rules:

- Prefer Python test code over shell scripts for assertions.
- Prefer `requests.Session()` over raw `curl`.
- The default automated path should not wipe the environment unless the
  caller explicitly selects fresh-start mode.
- Keep command execution granular. A normal discrete test action should
  usually complete in 60 seconds or less.
- If a flow naturally takes longer than that, break it into smaller
  observable steps unless the long wait is inherent to a build,
  deployment, or similar heavy operation.
- Use a router-attached test runner container by default for
  integration-like tests.
- Simple unit tests may run inside the relevant service container or via
  the repo's normal test runner.
- Claim student lanes through the real router or real lab API instead of
  bypassing lane-service.
- Capture enough failure data to debug the problem quickly:
  response status, headers, body excerpts, logs, and resolved container
  identity when relevant.

## Agent Playbook Standard

Agent tests are reusable playbooks that a human or an MCP-capable agent
can both follow.

Every playbook should include:

- prerequisites
- default non-destructive entry steps
- optional fresh-start reset and startup steps
- how to obtain credentials
- exact routes to open
- exact actions to perform
- exact commands to run
- expected result for each step
- what evidence to capture on failure
- how to record console and network errors

Rules:

- Use a fresh browser context unless the step explicitly tests resume
  behavior.
- When switching between student and instructor roles, discard the old
  browser context and create a brand-new session for the new role.
- Check JavaScript console errors and network failures after each major
  phase.
- Keep the playbook step size small enough that an agent is rarely
  waiting more than about 60 seconds on one discrete action.
- Prefer multiple short terminal or UI steps over one large opaque block
  of commands.
- Interact with ttyd through the live web path at least once.
- Do not "simulate" command success. The command must actually execute in
  the live terminal.
- If the page text instructs the student to run commands, the playbook
  should choose representative commands from that text and verify them.
- If the browser stage is intended to run in parallel, add a `suite.yaml`
  manifest that defines task ownership, context isolation, dependencies,
  and the report contract for each task.

## Coverage Checklist for a Lane-Managed TTYD Lab

Use this checklist for labs like Bitcoin, Consensus, and P2P Trust.

- default non-destructive entry path
- optional fresh-start reset path
- shared infra boot
- lab boot
- landing route
- claim route
- wrapper page
- lane resolution
- student ttyd route
- student supplemental surfaces
- instructor admin route
- instructor ttyd route
- any shared tooling route such as explorer, mempool, or RPC
- at least one real command run in the lab environment
- at least one real ttyd interaction through the browser path
- second run after reset when fresh-start mode is being validated

## Test Authoring Rules

- Keep each suite deterministic.
- Avoid hidden dependencies on other labs.
- Make setup explicit.
- Make teardown explicit.
- Make failures readable.
- Prefer fewer high-value assertions over shallow noise.
- If a test cannot be fully automated, document why and move the missing
  coverage into the agent playbook.

## Naming Guidance

Recommended naming:

- `regression-tests/automated/<lab>/test_*.py`
- `regression-tests/automated/<lab>/README.md`
- `regression-tests/agent/<lab>/playbook.md`
- `regression-tests/agent/<lab>/suite.yaml`
- `regression-tests/agent/<lab>/tasks/*.md`

Each lab directory should state:

- what it owns
- how it resets the lab
- how it boots the lab
- what is automated
- what remains agent-driven

## Definition of Done

A lab regression effort is not done until all of the following exist:

- a documented default non-destructive entry procedure
- a documented optional fresh-start reset procedure
- automated smoke coverage
- automated HTTP or integration coverage
- command verification against the real environment
- ttyd verification through the real web path
- instructor-surface coverage, if applicable
- a reusable agent playbook
