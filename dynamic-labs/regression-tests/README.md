# Regression Tests

This tree holds regression coverage for `dynamic-labs`.

- `automated/` is for code-driven tests.
- `agent/` is for reusable playbooks that a human or MCP-capable agent
  can follow.
- `infrastructure/` is for reusable local harnesses that help emulate
  deployment conditions during regression work.

The authoring standard lives in
`how-to-write-a-lab-regression-test.md`.

Each lab owns its own subdirectory under both trees.
