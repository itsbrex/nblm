#!/usr/bin/env python3
"""Unified nblm CLI with grouped commands, flat aliases, and verb-first aliases."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from typing import Dict, List, Optional, Sequence, Tuple

import alias_manager
import artifact_manager
import auth_manager
import config_manager
import doctor_manager
import export_manager
import query_manager
import research_manager
import setup_manager
import share_manager
import skill_manager
import source_manager
from notebook_manager import NotebookLibrary, extract_notebook_id
from notebooklm_wrapper import NotebookLMError, NotebookLMWrapper


GROUPS = [
    "login",
    "notebook",
    "source",
    "query",
    "research",
    "audio",
    "report",
    "quiz",
    "flashcards",
    "mindmap",
    "slides",
    "infographic",
    "video",
    "data-table",
    "alias",
    "config",
    "doctor",
    "setup",
    "skill",
    "share",
    "export",
    "download",
]

VERB_ALIASES = {
    ("create", "notebook"): ["notebook", "create"],
    ("create", "audio"): ["audio", "create"],
    ("create", "report"): ["report", "create"],
    ("create", "quiz"): ["quiz", "create"],
    ("create", "flashcards"): ["flashcards", "create"],
    ("create", "mindmap"): ["mindmap", "create"],
    ("create", "slides"): ["slides", "create"],
    ("create", "infographic"): ["infographic", "create"],
    ("create", "video"): ["video", "create"],
    ("create", "data-table"): ["data-table", "create"],
    ("list", "notebook"): ["notebook", "list"],
    ("list", "source"): ["source", "list"],
    ("list", "audio"): ["audio", "list"],
    ("list", "report"): ["report", "list"],
    ("list", "quiz"): ["quiz", "list"],
    ("list", "flashcards"): ["flashcards", "list"],
    ("list", "mindmap"): ["mindmap", "list"],
    ("list", "slides"): ["slides", "list"],
    ("list", "infographic"): ["infographic", "list"],
    ("list", "video"): ["video", "list"],
    ("list", "data-table"): ["data-table", "list"],
    ("get", "notebook"): ["notebook", "get"],
    ("get", "source"): ["source", "get"],
    ("delete", "notebook"): ["notebook", "delete"],
    ("delete", "source"): ["source", "delete"],
    ("delete", "audio"): ["audio", "delete"],
    ("delete", "report"): ["report", "delete"],
    ("delete", "quiz"): ["quiz", "delete"],
    ("delete", "flashcards"): ["flashcards", "delete"],
    ("delete", "mindmap"): ["mindmap", "delete"],
    ("delete", "slides"): ["slides", "delete"],
    ("delete", "infographic"): ["infographic", "delete"],
    ("delete", "video"): ["video", "delete"],
    ("delete", "data-table"): ["data-table", "delete"],
    ("add", "source"): ["source", "add"],
    ("add", "notebook"): ["notebook", "create"],
    ("rename", "notebook"): ["notebook", "rename"],
    ("rename", "source"): ["source", "rename"],
    ("status", "research"): ["research", "status"],
    ("status", "share"): ["share", "status"],
    ("describe", "notebook"): ["notebook", "describe"],
    ("describe", "source"): ["source", "describe"],
    ("sync", "source"): ["source", "sync"],
    ("content", "source"): ["source", "content"],
    ("stale", "source"): ["source", "stale"],
    ("install", "skill"): ["skill", "install"],
    ("uninstall", "skill"): ["skill", "uninstall"],
    ("update", "skill"): ["skill", "update"],
}


FLAT_ALIASES = {
    "notebooks": ["notebook", "list"],
    "summary": ["notebook", "summary"],
    "describe": ["notebook", "describe"],
    "sources": ["source", "list"],
    "upload-url": ["source", "add", "--url"],
    "upload-youtube": ["source", "add-youtube"],
    "upload-text": ["source", "add-text"],
    "source-text": ["source", "content"],
    "source-guide": ["source", "describe"],
    "source-rename": ["source", "rename"],
    "source-refresh": ["source", "sync"],
    "source-delete": ["source", "delete"],
    "podcast": ["audio", "create"],
    "ask": ["query", "ask"],
    "media-list": ["artifact", "list"],
    "media-delete": ["artifact", "delete"],
    "briefing": ["audio", "create", "--format", "BRIEF"],
    "debate": ["audio", "create", "--format", "DEBATE"],
    "slides": ["slides", "create"],
    "infographic": ["infographic", "create"],
    "podcast-status": ["audio", "status"],
    "podcast-download": ["audio", "download"],
    "slides-download": ["slides", "download"],
    "infographic-download": ["infographic", "download"],
}


ARTIFACT_TYPE_MAP = {
    "audio": "audio",
    "video": "video",
    "slides": "slide-deck",
    "infographic": "infographic",
    "report": "report",
    "mindmap": "mind-map",
    "data-table": "data-table",
    "quiz": "quiz",
    "flashcards": "flashcards",
}


ARTIFACT_CREATE_COMMAND = {
    "audio": "generate",
    "video": "generate-video",
    "slides": "generate-slides",
    "infographic": "generate-infographic",
    "report": "generate-report",
    "mindmap": "generate-mindmap",
    "data-table": "generate-data-table",
    "quiz": "generate-quiz",
    "flashcards": "generate-flashcards",
}


GROUP_HELP: Dict[str, str] = {
    "login": "Auth lifecycle and account profiles",
    "notebook": "Notebook CRUD, list/get/summary/describe",
    "source": "Source add/list/content/rename/sync/stale",
    "query": "Ask NotebookLM with source/conversation controls",
    "research": "Research start/status/import",
    "audio": "Audio artifact create/list/status/download/delete",
    "report": "Report artifact create/list/status/download/delete",
    "quiz": "Quiz artifact create/list/status/download/delete",
    "flashcards": "Flashcards create/list/status/download/delete",
    "mindmap": "Mind map create/list/status/download/delete",
    "slides": "Slide deck create/revise/list/status/download/delete",
    "infographic": "Infographic create/list/status/download/delete",
    "video": "Video create/list/status/download/delete",
    "data-table": "Data table create/list/status/download/delete",
    "alias": "Alias set/get/list/delete",
    "config": "Config show/get/set",
    "doctor": "Environment diagnostics",
    "setup": "Platform setup add/remove/list",
    "skill": "Skill install/uninstall/update/list/show",
    "share": "Share status/public/private/invite",
    "export": "Export artifacts to Docs/Sheets",
    "download": "Generic artifact downloads",
}


class CLIError(Exception):
    """CLI routing error."""



def print_help() -> None:
    print("nblm_cli - Unified NotebookLM CLI")
    print()
    print("Usage:")
    print("  nblm_cli.py [--json] [--quiet] [--confirm] <group> <subcommand> [args]")
    print("  nblm_cli.py <legacy-command> [args]")
    print("  nblm_cli.py <verb> <noun> [args]")
    print()
    print("Groups:")
    for group in GROUPS:
        print(f"  {group:<12} {GROUP_HELP.get(group, '')}")
    print("  artifact     Generic artifact routes (compatibility)")
    print()
    print("Verb aliases:")
    print("  create/list/get/delete/add/rename/status/describe/sync/content/stale/install/uninstall/update")



def _with_module_argv(module, argv: Sequence[str]) -> int:
    original = sys.argv
    sys.argv = [module.__file__, *argv]
    try:
        result = module.main()
        return int(result or 0)
    finally:
        sys.argv = original



def _normalize_token(token: str) -> str:
    return token.lower().strip()



def normalize_command(tokens: Sequence[str]) -> List[str]:
    if not tokens:
        return []

    parts = list(tokens)
    head = _normalize_token(parts[0])

    # legacy flat aliases
    if head in FLAT_ALIASES:
        return [*FLAT_ALIASES[head], *parts[1:]]

    # legacy notebook commands that conflict with verb aliases
    if head == "create" and (len(parts) == 1 or _normalize_token(parts[1]) not in {key[1] for key in VERB_ALIASES}):
        return ["notebook", "create", *parts[1:]]
    if head == "delete" and (len(parts) == 1 or _normalize_token(parts[1]) not in {key[1] for key in VERB_ALIASES}):
        return ["notebook", "delete", *parts[1:]]
    if head == "rename" and (len(parts) == 1 or _normalize_token(parts[1]) not in {key[1] for key in VERB_ALIASES}):
        return ["notebook", "rename", *parts[1:]]

    # special legacy sync alias
    if head == "sync":
        if len(parts) > 1:
            return ["source", "sync-folder", *parts[1:]]
        return ["source", "sync-folder"]

    # verb-first aliases
    if len(parts) >= 2:
        key = (_normalize_token(parts[0]), _normalize_token(parts[1]))
        mapped = VERB_ALIASES.get(key)
        if mapped:
            return [*mapped, *parts[2:]]

    return parts



def resolve_notebook_id(notebook_ref: Optional[str], use_active: bool = True) -> str:
    alias_store = alias_manager.AliasStore()
    if notebook_ref:
        notebook_ref = alias_store.resolve(notebook_ref, object_type="notebook")

    library = NotebookLibrary()

    if notebook_ref:
        notebook = library.get_notebook(notebook_ref)
        if notebook:
            extracted = extract_notebook_id(notebook.get("url", ""))
            return extracted or notebook_ref
        extracted = extract_notebook_id(notebook_ref)
        return extracted or notebook_ref

    if not use_active:
        raise CLIError("Notebook ID is required")

    active = library.get_active_notebook()
    if not active:
        raise CLIError("No active notebook. Use notebook list or provide --id.")
    extracted = extract_notebook_id(active.get("url", ""))
    return extracted or active.get("id")



def _maybe_suppress_output(quiet: bool):
    if quiet:
        return redirect_stdout(StringIO())
    return redirect_stdout(sys.stdout)


async def handle_notebook(tokens: Sequence[str], json_output: bool, quiet: bool) -> int:
    parser = argparse.ArgumentParser(prog="notebook")
    subparsers = parser.add_subparsers(dest="sub")

    p = subparsers.add_parser("list")
    p.add_argument("--format", choices=["table", "json"], default="table")

    p = subparsers.add_parser("create")
    p.add_argument("name")

    p = subparsers.add_parser("get")
    p.add_argument("id", nargs="?")

    p = subparsers.add_parser("delete")
    p.add_argument("--id")

    p = subparsers.add_parser("rename")
    p.add_argument("name")
    p.add_argument("--id")

    p = subparsers.add_parser("summary")
    p.add_argument("--id")

    p = subparsers.add_parser("describe")
    p.add_argument("--id")

    if not tokens:
        parser.print_help()
        return 1

    args = parser.parse_args(tokens)

    async with NotebookLMWrapper() as wrapper:
        if args.sub == "list":
            notebooks = await wrapper.list_notebooks()
            if json_output or args.format == "json":
                print(json.dumps({"notebooks": notebooks}, indent=2, ensure_ascii=False))
            else:
                for nb in notebooks:
                    print(f"{nb.get('id')}\t{nb.get('title')}")
            return 0

        if args.sub == "create":
            result = await wrapper.create_notebook(args.name)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "get":
            notebook_id = resolve_notebook_id(args.id)
            notebooks = await wrapper.list_notebooks()
            found = None
            for nb in notebooks:
                if nb.get("id") == notebook_id:
                    found = nb
                    break
            if not found:
                raise CLIError(f"Notebook not found: {notebook_id}")
            print(json.dumps(found, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "delete":
            notebook_id = resolve_notebook_id(args.id)
            await wrapper.delete_notebook(notebook_id)
            print(json.dumps({"success": True, "deleted": notebook_id}, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "rename":
            notebook_id = resolve_notebook_id(args.id)
            result = await wrapper.rename_notebook(notebook_id, args.name)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "summary":
            notebook_id = resolve_notebook_id(args.id)
            summary = await wrapper.get_notebook_summary(notebook_id)
            if json_output:
                print(json.dumps({"summary": summary}, indent=2, ensure_ascii=False))
            else:
                print(summary)
            return 0

        if args.sub == "describe":
            notebook_id = resolve_notebook_id(args.id)
            desc = await wrapper.get_notebook_description(notebook_id)
            print(json.dumps(desc, indent=2, ensure_ascii=False))
            return 0

    return 1


async def handle_source(tokens: Sequence[str], json_output: bool, quiet: bool) -> int:
    parser = argparse.ArgumentParser(prog="source")
    subparsers = parser.add_subparsers(dest="sub")

    p = subparsers.add_parser("list")
    p.add_argument("--id")

    p = subparsers.add_parser("add")
    p.add_argument("--url")
    p.add_argument("--file")
    p.add_argument("--drive")
    p.add_argument("--title")
    p.add_argument("--doc-type", default="doc")
    p.add_argument("--notebook-id")
    p.add_argument("--use-active", action="store_true")
    p.add_argument("--create-new", action="store_true")

    p = subparsers.add_parser("add-youtube")
    p.add_argument("url")
    p.add_argument("--id")

    p = subparsers.add_parser("add-text")
    p.add_argument("title")
    p.add_argument("--content")
    p.add_argument("--id")

    p = subparsers.add_parser("get")
    p.add_argument("source_id")
    p.add_argument("--id")

    p = subparsers.add_parser("content")
    p.add_argument("source_id")
    p.add_argument("--id")

    p = subparsers.add_parser("describe")
    p.add_argument("source_id")
    p.add_argument("--id")

    p = subparsers.add_parser("rename")
    p.add_argument("source_id")
    p.add_argument("name")
    p.add_argument("--id")

    p = subparsers.add_parser("sync")
    p.add_argument("source_id")
    p.add_argument("--id")

    p = subparsers.add_parser("delete")
    p.add_argument("source_id")
    p.add_argument("--id")

    p = subparsers.add_parser("stale")
    p.add_argument("--notebook-id")

    p = subparsers.add_parser("sync-drive")
    p.add_argument("--notebook-id")
    p.add_argument("--source-ids")

    p = subparsers.add_parser("sync-folder")
    p.add_argument("folder")
    p.add_argument("--notebook-id")
    p.add_argument("--use-active", action="store_true")
    p.add_argument("--create-new", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rebuild", action="store_true")

    if not tokens:
        parser.print_help()
        return 1

    args = parser.parse_args(tokens)

    if args.sub in {"add", "stale", "sync-drive", "sync-folder"}:
        relay = []
        if args.sub == "sync-folder":
            relay = ["sync", args.folder]
            if args.notebook_id:
                relay.extend(["--notebook-id", args.notebook_id])
            if args.use_active:
                relay.append("--use-active")
            if args.create_new:
                relay.append("--create-new")
            if args.dry_run:
                relay.append("--dry-run")
            if args.rebuild:
                relay.append("--rebuild")
        elif args.sub == "add":
            relay = ["add"]
            for key in ["url", "file", "drive", "title", "doc_type", "notebook_id"]:
                value = getattr(args, key)
                if value:
                    flag = "--doc-type" if key == "doc_type" else f"--{key.replace('_', '-') }"
                    relay.extend([flag, str(value)])
            if args.use_active:
                relay.append("--use-active")
            if args.create_new:
                relay.append("--create-new")
        elif args.sub == "stale":
            relay = ["stale"]
            if args.notebook_id:
                relay.extend(["--notebook-id", args.notebook_id])
        elif args.sub == "sync-drive":
            relay = ["sync-drive"]
            if args.notebook_id:
                relay.extend(["--notebook-id", args.notebook_id])
            if args.source_ids:
                relay.extend(["--source-ids", args.source_ids])
        return _with_module_argv(source_manager, relay)

    notebook_id = resolve_notebook_id(getattr(args, "id", None))

    async with NotebookLMWrapper() as wrapper:
        if args.sub == "list":
            notebook_id = resolve_notebook_id(args.id)
            sources = await wrapper.list_sources(notebook_id)
            print(json.dumps({"sources": sources}, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "add-youtube":
            result = await wrapper.add_youtube(notebook_id, args.url)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "add-text":
            content = args.content or sys.stdin.read()
            result = await wrapper.add_text(notebook_id, args.title, content)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "get":
            result = await wrapper.get_source(notebook_id, args.source_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "content":
            result = await wrapper.get_source_fulltext(notebook_id, args.source_id)
            if json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(result.get("content", ""))
            return 0

        if args.sub == "describe":
            result = await wrapper.get_source_guide(notebook_id, args.source_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "rename":
            result = await wrapper.rename_source(notebook_id, args.source_id, args.name)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "sync":
            result = await wrapper.sync_source(notebook_id, args.source_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.sub == "delete":
            await wrapper.delete_source(notebook_id, args.source_id)
            print(json.dumps({"success": True, "deleted": args.source_id}, indent=2, ensure_ascii=False))
            return 0

    return 1



def _translate_artifact_group(group: str, tokens: Sequence[str]) -> List[str]:
    sub = tokens[0] if tokens else "create"
    rest = list(tokens[1:]) if tokens else []
    artifact_type = ARTIFACT_TYPE_MAP[group]

    if sub == "create":
        return [ARTIFACT_CREATE_COMMAND[group], *rest]
    if sub == "revise" and group == "slides":
        return ["revise-slides", *rest]
    if sub == "list":
        return ["list", "--type", artifact_type, *rest]
    if sub == "get":
        return ["get", *rest]
    if sub == "delete":
        return ["delete", *rest]
    if sub == "status":
        if rest and not rest[0].startswith("-") and "--task-id" not in rest:
            return ["status", "--task-id", rest[0], *rest[1:]]
        return ["status", *rest]
    if sub == "download":
        return ["download", *rest, "--type", artifact_type]

    raise CLIError(f"Unsupported {group} command: {sub}")



def handle_artifact_group(group: str, tokens: Sequence[str]) -> int:
    if not tokens or tokens[0] in {"-h", "--help"}:
        suffix = ", revise" if group == "slides" else ""
        print(f"{group} commands: create, list, get, delete, status, download{suffix}")
        print(f"Example: nblm_cli.py {group} create --wait")
        return 0
    translated = _translate_artifact_group(group, tokens)
    return _with_module_argv(artifact_manager, translated)



def handle_download(tokens: Sequence[str]) -> int:
    if tokens and tokens[0] in {"-h", "--help"}:
        print("Usage: nblm_cli.py download <type> <output> [--artifact-id ID] [--notebook-id ID]")
        print("Types: audio, video, slide-deck, infographic, report, mind-map, data-table, quiz, flashcards")
        return 0
    if not tokens:
        raise CLIError("Usage: download <type> <output> [--artifact-id ID] [--notebook-id ID]")
    artifact_type = tokens[0]
    rest = list(tokens[1:])
    if artifact_type not in ARTIFACT_TYPE_MAP.values() and artifact_type not in ARTIFACT_TYPE_MAP:
        raise CLIError(f"Unsupported download type: {artifact_type}")
    canonical_type = ARTIFACT_TYPE_MAP.get(artifact_type, artifact_type)
    return _with_module_argv(artifact_manager, ["download", *rest, "--type", canonical_type])



def handle_login(tokens: Sequence[str]) -> int:
    if not tokens:
        return _with_module_argv(auth_manager, ["setup", "--service", "google"])

    sub = tokens[0]
    rest = list(tokens[1:])

    if sub == "status":
        return _with_module_argv(auth_manager, ["status", *rest])
    if sub in {"check", "--check"}:
        service = "google"
        if "--provider" in rest:
            idx = rest.index("--provider")
            if idx + 1 < len(rest):
                service = rest[idx + 1]
        return _with_module_argv(auth_manager, ["validate", "--service", service])
    if sub == "clear":
        return _with_module_argv(auth_manager, ["clear", *rest])
    if sub == "reauth":
        return _with_module_argv(auth_manager, ["reauth", *rest])
    if sub == "accounts":
        return _with_module_argv(auth_manager, ["accounts", *rest])
    if sub == "setup":
        return _with_module_argv(auth_manager, ["setup", *rest])

    # default shorthand: login [--provider google]
    provider = "google"
    args = list(tokens)
    if "--provider" in args:
        idx = args.index("--provider")
        if idx + 1 < len(args):
            provider = args[idx + 1]
            del args[idx : idx + 2]
    if "--fresh" in args:
        args.remove("--fresh")
        return _with_module_argv(auth_manager, ["setup", "--service", provider, "--fresh", *args])
    return _with_module_argv(auth_manager, ["setup", "--service", provider, *args])



def handle_group(group: str, tokens: Sequence[str], json_output: bool, quiet: bool, confirm: bool) -> int:
    if group == "login":
        return handle_login(tokens)
    if group == "notebook":
        return asyncio.run(handle_notebook(tokens, json_output=json_output, quiet=quiet))
    if group == "source":
        return asyncio.run(handle_source(tokens, json_output=json_output, quiet=quiet))
    if group == "query":
        relay = list(tokens)
        if not relay or relay[0].startswith("-"):
            relay = ["ask", *relay]
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(query_manager, relay)
    if group == "research":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(research_manager, relay)
    if group in ARTIFACT_TYPE_MAP:
        return handle_artifact_group(group, tokens)
    if group == "artifact":
        return _with_module_argv(artifact_manager, list(tokens))
    if group == "alias":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(alias_manager, relay)
    if group == "config":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(config_manager, relay)
    if group == "doctor":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(doctor_manager, relay)
    if group == "setup":
        return _with_module_argv(setup_manager, list(tokens))
    if group == "skill":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(skill_manager, relay)
    if group == "share":
        relay = list(tokens)
        if confirm and relay and relay[0] in {"public", "private"} and "--confirm" not in relay:
            relay.append("--confirm")
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(share_manager, relay)
    if group == "export":
        relay = list(tokens)
        if json_output and "--json" not in relay:
            relay = ["--json", *relay]
        return _with_module_argv(export_manager, relay)
    if group == "download":
        return handle_download(tokens)

    raise CLIError(f"Unknown command group: {group}")



def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("tokens", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.help:
        print_help()
        return 0

    normalized = normalize_command(args.tokens)
    if not normalized:
        print_help()
        return 1

    group = normalized[0]
    tokens = normalized[1:]

    if group not in GROUPS and group != "artifact":
        print(f"❌ Unknown command: {' '.join(args.tokens)}", file=sys.stderr)
        print_help()
        return 1

    try:
        if args.quiet:
            with _maybe_suppress_output(True):
                return handle_group(group, tokens, args.json, args.quiet, args.confirm)
        return handle_group(group, tokens, args.json, args.quiet, args.confirm)
    except NotebookLMError as err:
        print(f"❌ [{err.code}] {err.message}", file=sys.stderr)
        if err.recovery:
            print(f"🔧 {err.recovery}", file=sys.stderr)
        return 1
    except CLIError as err:
        print(f"❌ {err}", file=sys.stderr)
        return 1
    except SystemExit as err:
        # Preserve parser exits from delegated modules
        return int(err.code or 0)
    except Exception as err:
        print(f"❌ Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
