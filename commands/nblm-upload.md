---
description: Upload a file or URL to NotebookLM
argument-hint: <file-path-or-url> [--notebook-id ID]
allowed-tools: Bash, Read
---

Upload a source to NotebookLM. Accepts local files (PDF, TXT, MD), web URLs, and Z-Library URLs.

$IF($1,
  Determine if "$1" is a file path or URL:
  - If it's a local file path: Run grouped CLI: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py source add --file "$1" $ARGUMENTS`
  - If it's a URL: Run grouped CLI: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py nblm_cli.py source add --url "$1" $ARGUMENTS`
  - Legacy fallback still supported: !`cd ${CLAUDE_PLUGIN_ROOT} && python scripts/run.py source_manager.py add --file "$1" $ARGUMENTS`

  Report the upload result including the notebook ID and source title.,

  ERROR: Please provide a file path or URL. Usage: /nblm-upload <file-or-url> [--notebook-id ID]
)
