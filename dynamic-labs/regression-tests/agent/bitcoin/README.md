# Bitcoin Agent Regression

This directory holds the reusable browser-driven playbook plus the task
manifest for the Bitcoin lab.

Target coverage:

- default non-destructive browser entry
- optional fresh-start reference
- student journey through `/labs/bitcoin/`
- wrapper page behavior
- live ttyd interaction through the real web route
- page-derived commands run from both Lab 1 and Lab 2 through the
  browser terminal
- mempool, explorer, static, and peers checks
- instructor admin and instructor ttyd checks
- JavaScript and network error capture throughout the flow

Artifacts:

- `playbook.md` - single-agent sequential browser playbook
- `suite.yaml` - task manifest for multi-agent orchestration
- `tasks/*.md` - per-task instructions for separate MCP agents or
  browser contexts
- `report-template.md` - expected task return format
