---
description: Show NotebookLM authentication and library status
allowed-tools: Bash
---

Show the current authentication status and active notebook.

Run these commands:
1. !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py login status`
2. !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py notebook_manager.py list`

Summarize:
- Authentication status (Google, Z-Library)
- Active notebook (if any)
- Total notebooks in library
