# Consensus Agent Regression

This directory holds the reusable browser playbook and task manifest for
the Consensus lab.

Target coverage:

- default non-destructive browser entry
- optional fresh-start reference for when the live environment is not
  trustworthy
- student claim and wrapper flow
- wrapper affordances, including the `help-btn`
- visible guide/tabs content for the PoW and PoS exercises
- page-derived command coverage across the visible PoW and PoS labs
- instructor auth gate verification and instructor-only surfaces

Artifacts:

- `playbook.md` - single-agent sequential browser playbook
- `suite.yaml` - task manifest for browser-MCP orchestration
- `tasks/*.md` - per-task instructions for separate MCP agents or
  browser contexts

Scope split:

- the automated suite still owns deeper deterministic verification
- this browser suite now requires page-derived command execution for the
  visible PoW and PoS command blocks, in addition to UI rendering and
  auth gates
