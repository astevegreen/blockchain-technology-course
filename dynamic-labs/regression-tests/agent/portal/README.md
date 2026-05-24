# Shared Instructor Portal Regression

This directory holds the browser-driven regression suite for shared
instructor portal surfaces that are not owned by one lab.

Current scope:

- `/instructor/labs-progress`
- `/api/portal/progress-rollup`

Files:

- `playbook.md` - single-agent end-to-end flow
- `suite.yaml` - task manifest for browser-MCP runs
- `tasks/*.md` - per-task instructions for isolated browser contexts
