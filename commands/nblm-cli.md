---
description: Unified grouped nblm CLI (noun-first + verb aliases)
allowed-tools: Bash, Read
---

Use the unified grouped CLI surface for NotebookLM operations.

Run help:
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py --help`

Examples:

- Notebook list:
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py notebook list`

- Source add (URL):
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py source add --url "https://example.com" --use-active`

- Query:
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py query ask "What are the key findings?" --timeout 120`

- Research:
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py research start "AI trends" --mode deep`

- Report generation:
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py report create --wait --output ./report.md`

- Verb alias (equivalent):
!`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py create report --wait --output ./report.md`
