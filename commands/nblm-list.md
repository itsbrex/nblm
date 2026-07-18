---
description: List all notebooks in your NotebookLM library
allowed-tools: Bash
---

List notebooks using the unified grouped CLI surface.

Preferred: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py notebook list`

Verb alias equivalent: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py list notebook`

Legacy local-library fallback: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py notebook_manager.py list`

Display the results in a clean format showing notebook names, IDs, and which one is active.
