# P2P Trust Agent Regression

This directory holds the reusable browser playbook and task manifest
for the `p2p_trust` lab.

Target coverage:

- default non-destructive browser entry
- optional fresh-start reference for when the live environment is not
  trustworthy
- student claim and wrapper flow
- wrapper affordances, including the `help-btn`
- visible guide content for the Reputation and Routing labs
- page-derived command coverage across the visible Reputation and
  Routing labs
- instructor auth gate verification and instructor-only surfaces

Artifacts:

- `playbook.md` - single-agent sequential browser playbook
- `suite.yaml` - task manifest for browser-MCP orchestration
- `tasks/*.md` - per-task instructions for separate MCP agents or
  browser contexts

Scope split:

- deterministic backend verification still lives in the automated suite
- this browser suite now requires page-derived command execution for the
  visible Reputation and Routing command blocks, in addition to UI and
  auth checks
