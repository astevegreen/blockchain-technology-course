# Cryptography Agent Regression

This directory holds the browser-driven regression suite for the
Cryptography lab.

Use it after the automated suite passes. The browser stage covers the
Streamlit-specific behaviors that are awkward or impossible to validate
 with `requests` alone:

- student landing and redirect into the app
- module and scenario navigation inside Streamlit
- visible command text versus actual command behavior
- browser console errors and network failures
- instructor console rendering and guide visibility

Primary entry points:

- `playbook.md` - single-agent end-to-end flow
- `suite.yaml` - multi-agent task manifest for MCP/browser runs

