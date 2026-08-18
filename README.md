<div align="center">

**English** | [中文](README.zh-CN.md)

# nblm

### Your AI Coding Agent's Gateway to NotebookLM

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-purple.svg)](https://github.com/vercel-labs/add-skill)
[![License](https://img.shields.io/github/license/magicseek/nblm)](LICENSE)

<br/>

🧠 **Zero Hallucinations** — Answers grounded exclusively in your documents
<br/>
⚡ **Zero Context Switching** — Ask, upload, generate podcasts & slides from your editor
<br/>
🔌 **Infinite Sources** — Z-Library today, arXiv / Notion / Confluence tomorrow

<br/>

<sub>Works with **Claude Code** · **Cursor** · **Windsurf** · **Codex** · and any [Agent Skills](https://github.com/vercel-labs/add-skill) compatible agent</sub>

<br/>

[Installation](#installation) · [Quick Start](#quick-start) · [Commands](#commands) · [Architecture](#architecture)

</div>

---

## Installation

### Recommended: Using add-skill CLI

```bash
npx add-skill magicseek/nblm
```

This works with any supported agent. To install for a specific agent:

```bash
# Claude Code only
npx add-skill magicseek/nblm -a claude-code

# Global installation (available across all projects)
npx add-skill magicseek/nblm --global

# Multiple agents
npx add-skill magicseek/nblm -a claude-code -a cursor -a opencode
```

### Local: Install from a local clone

If you've already cloned this repo (or are developing on it), point `add-skill` at
the local folder instead of the `magicseek/nblm` GitHub shorthand:

```bash
# From inside the repo (installs the current folder)
npx add-skill .

# From anywhere (absolute or relative path to the clone)
npx add-skill ~/github/nblm
npx add-skill ./nblm

# Local install for a specific agent
npx add-skill . -a claude-code

# Local global installation (available across all projects)
npx add-skill . --global

# Local install for multiple agents
npx add-skill . -a claude-code -a cursor -a opencode
```

### Updating a global install

If the skill was registered from GitHub (e.g. `npx skills add -g magicseek/nblm -y`),
the skills CLI can check for and apply updates:

```bash
# Preferred: authenticates via the gh CLI first, then falls back to
# GITHUB_TOKEN / GH_TOKEN, then unauthenticated
npm run skill:update

# Equivalent manual invocation
GITHUB_TOKEN="$(gh auth token)" npx skills update -g
```

Notes:
- Updates track the **default branch** of the registered source repo.
- The install folder is wiped and re-copied on every update. User data is safe:
  it lives in `~/.nblm/data/` (or `NBLM_DATA_DIR`), outside the install folder.
- Local-path installs (`npx add-skill .`) are not update-checkable — re-run the
  local install instead.

### Alternative: Platform-specific initialization

If symlinks created by `add-skill` don't work well in your environment (e.g., Cursor, Windows), you can generate platform-specific files directly:

**macOS / Linux:**
```bash
# Clone the repo
git clone https://github.com/magicseek/nblm ~/.nblm

# Initialize for your AI assistant (run from your project directory)
python ~/.nblm/scripts/run.py init --ai cursor       # Cursor
python ~/.nblm/scripts/run.py init --ai claude       # Claude Code
python ~/.nblm/scripts/run.py init --ai codex        # Codex CLI
python ~/.nblm/scripts/run.py init --ai antigravity  # Antigravity
python ~/.nblm/scripts/run.py init --ai windsurf     # Windsurf
python ~/.nblm/scripts/run.py init --ai copilot      # GitHub Copilot
python ~/.nblm/scripts/run.py init --ai all          # All platforms

# List available platforms
python ~/.nblm/scripts/run.py init --list
```

**Windows (PowerShell):**
```powershell
# Clone the repo
git clone https://github.com/magicseek/nblm $env:USERPROFILE\.nblm

# Initialize for your AI assistant (run from your project directory)
python $env:USERPROFILE\.nblm\scripts\run.py init --ai cursor       # Cursor
python $env:USERPROFILE\.nblm\scripts\run.py init --ai claude       # Claude Code
python $env:USERPROFILE\.nblm\scripts\run.py init --ai codex        # Codex CLI
python $env:USERPROFILE\.nblm\scripts\run.py init --ai antigravity  # Antigravity
python $env:USERPROFILE\.nblm\scripts\run.py init --ai windsurf     # Windsurf
python $env:USERPROFILE\.nblm\scripts\run.py init --ai copilot      # GitHub Copilot
python $env:USERPROFILE\.nblm\scripts\run.py init --ai all          # All platforms

# List available platforms
python $env:USERPROFILE\.nblm\scripts\run.py init --list
```

This generates the appropriate skill/command files in your project directory (e.g., `.cursor/commands/nblm.md`).

### First Run

On first use, nblm automatically:
- Creates an isolated Python environment (`.venv`) via `uv venv`
- Syncs Python dependencies via `uv sync`
- Installs Node.js dependencies
- Starts the agent-browser daemon as needed

No manual setup required. If Playwright browsers are missing, run `npm run install-browsers` in the skill folder.

Manual setup (if automatic setup fails):

```bash
uv venv .venv
source .venv/bin/activate
uv sync
npm install
npm run install-browsers
```

### Dependency Migration to uv

If you are migrating an older clone that still uses `requirements.txt`, use:

```bash
# 1) Create pyproject.toml
uv init --bare

# 2) Import runtime requirements
uv add -r requirements.txt

# 3) Import dev requirements (if you have them)
uv add --dev -r requirements-dev.txt

# Verify imports
uv pip freeze

# 4) Remove old requirements files
rm requirements.txt requirements-dev.txt

# 5) Ongoing dependency management
uv add requests
uv add --dev pytest
uv remove requests
```

---

## Quick Start

### 1. Authenticate with Google (one-time)

```
/nblm login
```

A browser window opens for Google login. This is required once.

### 2. Add a notebook to your library

Go to [notebooklm.google.com](https://notebooklm.google.com) → Create notebook → Upload your docs → Share with "Anyone with link"

```
/nblm add <notebook-url-or-id>
```

nblm automatically queries the notebook to discover its content and metadata.

### 3. Ask questions

```
/nblm ask "What does the documentation say about authentication?"
```

Answers are source-grounded with citations from your uploaded documents.

### 4. Manage your notebooks

```
/nblm local          # List notebooks in your library
/nblm remote         # List all notebooks from NotebookLM API
/nblm status         # Show auth and library status
```

### 5. Upload sources

```
/nblm upload ./document.pdf           # Local file
/nblm upload-url https://example.com  # Web URL
/nblm upload-zlib <z-library-url>     # Z-Library book
```

---

## Commands

### Unified `nblm_cli` syntax (grouped + verb aliases)

`nblm` now supports grouped command routing (parity-style) while keeping legacy flat commands:

```bash
# Grouped style
python scripts/run.py nblm_cli.py notebook list
python scripts/run.py nblm_cli.py source add --url "https://example.com" --use-active
python scripts/run.py nblm_cli.py query ask "What are the key risks?" --source-ids src1,src2
python scripts/run.py nblm_cli.py research start "AI trends" --mode deep
python scripts/run.py nblm_cli.py report create --wait --output ./report.md
python scripts/run.py nblm_cli.py share status
python scripts/run.py nblm_cli.py export create <artifact-id> --type docs

# Verb-first aliases
python scripts/run.py nblm_cli.py create report --wait --output ./report.md
python scripts/run.py nblm_cli.py list notebook
python scripts/run.py nblm_cli.py stale source --notebook-id <id>
```

Supported main groups include:
`login`, `notebook`, `source`, `query`, `research`, `audio`, `report`, `quiz`,
`flashcards`, `mindmap`, `slides`, `infographic`, `video`, `data-table`,
`alias`, `config`, `doctor`, `setup`, `skill`, `share`, `export`, `download`.

Legacy commands like `/nblm podcast`, `/nblm ask`, `/nblm upload-url`, and `/nblm source-refresh` remain supported as aliases.

<details>
<summary><strong>📚 Notebook Management</strong></summary>

| Command | Description |
|---------|-------------|
| `/nblm login` | Authenticate with Google |
| `/nblm accounts` | List all Google accounts |
| `/nblm accounts add` | Add a new Google account |
| `/nblm accounts switch <id>` | Switch active account (by index or email) |
| `/nblm accounts remove <id>` | Remove an account |
| `/nblm status` | Show auth and library status |
| `/nblm local` | List notebooks in local library |
| `/nblm remote` | List all notebooks from NotebookLM API |
| `/nblm create <name>` | Create a new notebook |
| `/nblm delete [--id ID]` | Delete a notebook |
| `/nblm rename <name> [--id ID]` | Rename a notebook |
| `/nblm summary [--id ID]` | Get AI-generated summary |
| `/nblm describe [--id ID]` | Get description and suggested topics |
| `/nblm add <url-or-id>` | Add notebook to local library |
| `/nblm activate <id>` | Set active notebook |

</details>

<details>
<summary><strong>📄 Source Management</strong></summary>

| Command | Description |
|---------|-------------|
| `/nblm sources [--id ID]` | List sources in notebook |
| `/nblm upload <file>` | Upload local file (PDF, TXT, MD, DOCX) |
| `/nblm upload-zlib <url>` | Download from Z-Library and upload |
| `/nblm upload-url <url>` | Add URL as source |
| `/nblm upload-youtube <url>` | Add YouTube video as source |
| `/nblm upload-text <title> [--content TEXT]` | Add text as source |
| `/nblm source-text <source-id>` | Get full indexed text |
| `/nblm source-guide <source-id>` | Get AI summary and keywords |
| `/nblm source-rename <source-id> <name>` | Rename a source |
| `/nblm source-refresh <source-id>` | Re-fetch URL content |
| `/nblm source-delete <source-id>` | Delete a source |

</details>

<details>
<summary><strong>💬 Chat & Query</strong></summary>

| Command | Description |
|---------|-------------|
| `/nblm ask <question>` | Query NotebookLM |

</details>

<details>
<summary><strong>🎙️ Media Generation</strong></summary>

| Command | Description |
|---------|-------------|
| `/nblm podcast [--instructions TEXT]` | Generate audio podcast (deep-dive) |
| `/nblm podcast-status <task-id>` | Check podcast generation status |
| `/nblm podcast-download [output-path]` | Download latest podcast |
| `/nblm briefing [--instructions TEXT]` | Generate brief audio summary |
| `/nblm debate [--instructions TEXT]` | Generate debate-style audio |
| `/nblm slides [--instructions TEXT]` | Generate slide deck |
| `/nblm slides-download [output-path]` | Download slide deck as PDF |
| `/nblm infographic [--instructions TEXT]` | Generate infographic |
| `/nblm infographic-download [output-path]` | Download infographic |
| `/nblm media-list [--type TYPE]` | List generated media |
| `/nblm media-delete <id>` | Delete a generated media item |

**Media generation options:**

| Option | Values |
|--------|--------|
| `--length` | `SHORT`, `DEFAULT`, `LONG` |
| `--instructions` | Custom instructions for content |
| `--wait` | Wait for generation to complete |
| `--output` | Download path (requires `--wait`) |

</details>

---

## Architecture

nblm uses a hybrid approach combining API-first operations with browser automation fallback:

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Agent                           │
│              (Claude Code / Cursor / OpenCode)              │
└─────────────────────┬───────────────────────────────────────┘
                      │ /nblm commands
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                         nblm                                │
├─────────────────────┬───────────────────────────────────────┤
│   notebooklm-py     │         agent-browser                 │
│   (API operations)  │      (browser automation)             │
│                     │                                       │
│ • Create notebooks  │ • Google authentication               │
│ • Add sources       │ • File uploads (fallback)             │
│ • Chat queries      │ • Z-Library downloads                 │
│ • Generate media    │ • Future non-API sources              │
└─────────────────────┴───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Google NotebookLM                         │
│            (Gemini-powered document Q&A)                    │
└─────────────────────────────────────────────────────────────┘
```

**Key components:**

| Component | Role |
|-----------|------|
| **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** | Async Python client for NotebookLM API operations |
| **[agent-browser](https://github.com/vercel-labs/agent-browser)** | Headless browser daemon for auth and non-API sources |
| **scripts/run.py** | Entry point that auto-manages `uv venv` + `uv sync` and dependencies |

Python dependency source of truth: `pyproject.toml` + `uv.lock`.

**Data storage** (in `~/.nblm/data/` by default, override with `NBLM_DATA_DIR`):
- `library.json` — Your notebook metadata (with account associations)
- `auth/google/` — Multi-account Google authentication
  - `index.json` — Account index and active account
  - `<n>-<email>.json` — Per-account credentials
- `auth/zlibrary.json` — Z-Library authentication state

Data lives outside the skill install directory so skill updates (which wipe and
re-copy the install folder) never destroy auth or your notebook library. A
legacy in-repo `data/` folder is migrated automatically on first run.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Skill not found | Verify installation: `ls ~/.claude/skills/nblm/` |
| `ModuleNotFoundError` | Always use `/nblm` commands — they auto-manage the environment |
| Authentication fails | Run `/nblm login` with a visible browser |
| `DAEMON_UNAVAILABLE` | Ensure Node.js is installed, then run `npm install` in the skill folder |
| Rate limit (50/day) | Wait 24 hours or use a different Google account |
| Browser crashes | Run `python scripts/run.py cleanup_manager.py --preserve-library` |

For more details, see [references/troubleshooting.md](references/troubleshooting.md).

---

## Acknowledgments

nblm builds upon the excellent work of these projects:

- **[notebooklm-skill](https://github.com/PleasePrompto/notebooklm-skill)** by PleasePrompto — The original Claude Code skill for NotebookLM integration with browser automation
- **[zlibrary-to-notebooklm](https://github.com/zstmfhy/zlibrary-to-notebooklm)** by zstmfhy — Z-Library to NotebookLM pipeline
- **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** by teng-lin — Async Python API client for NotebookLM

Additional dependencies:
- **[agent-browser](https://github.com/vercel-labs/agent-browser)** — Headless browser daemon for AI agents
- **[add-skill](https://github.com/vercel-labs/add-skill)** — Universal skill installer for AI coding agents

---

## Limitations

- **Rate limits** — Free tier allows ~50 queries/day per Google account (use multiple accounts to increase limits)
- **No session persistence** — Each query is independent (no "previous answer" context)
- **Manual notebook creation** — You must create notebooks and upload docs via [notebooklm.google.com](https://notebooklm.google.com)

## License

MIT

---

<div align="center">

**nblm** — Source-grounded answers from your documents, directly in your coding agent.

[Report Issue](https://github.com/magicseek/nblm/issues) · [View on GitHub](https://github.com/magicseek/nblm)

</div>
