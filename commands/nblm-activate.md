---
description: Set the active notebook for queries
argument-hint: <notebook-id>
allowed-tools: Bash
---

Set a notebook as the active default for queries.

$IF($1,
  Run local-library activation:
  !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py notebook_manager.py activate --id "$1"`

  Grouped CLI query usage then uses active notebook by default:
  !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py query ask "test question"`

  Confirm which notebook is now active.,

  ERROR: Please provide a notebook ID. Usage: /nblm-activate <notebook-id>

  To see available notebooks, use /nblm-list
)
