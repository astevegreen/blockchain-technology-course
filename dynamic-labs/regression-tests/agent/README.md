# Agent Regression Playbooks

Reusable playbooks live here.

Rules:

- one lab per playbook, except for narrow shared platform surfaces that
  are not owned by a single lab
- human-readable and agent-readable
- include reset, startup, routes, actions, expected results, and failure
  evidence
- before browser/MCP phases on claim-limited labs, release stale claims
  so the agent is testing product behavior rather than an exhausted pool
- create a fresh browser context/session whenever switching between
  student and instructor roles
- check console and network failures during browser-driven validation
- validate ttyd through the real web path
- for command-bearing labs, prefer page-derived command execution over
  generic ttyd smoke coverage; if the page shows student commands, the
  agent should read those commands from the rendered page and run them
  through the browser terminal
- add `suite.yaml` plus `tasks/*.md` when the browser stage should be
  split across multiple agents or browser contexts
