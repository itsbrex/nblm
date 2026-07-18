#!/usr/bin/env python3
"""Research task manager for NotebookLM."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Optional

from alias_manager import AliasStore
from notebook_manager import NotebookLibrary, extract_notebook_id
from notebooklm_wrapper import NotebookLMError, NotebookLMWrapper



def resolve_notebook_id(notebook_id: Optional[str]) -> str:
    alias_store = AliasStore()
    candidate = alias_store.resolve(notebook_id, object_type="notebook") if notebook_id else None
    if candidate:
        return candidate

    library = NotebookLibrary()
    if notebook_id:
        notebook = library.get_notebook(notebook_id)
        if notebook:
            extracted = extract_notebook_id(notebook.get("url", ""))
            if extracted:
                return extracted
        return notebook_id

    active = library.get_active_notebook()
    if not active:
        raise ValueError("No active notebook. Use --notebook-id or activate one first.")
    extracted = extract_notebook_id(active.get("url", ""))
    return extracted or active.get("id")


async def cmd_start(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.start_research(
            notebook_id=notebook_id,
            query=args.query,
            source=args.source,
            mode=args.mode,
        )


async def cmd_status(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        payload = await wrapper.poll_research(notebook_id)
        payload["notebook_id"] = notebook_id
        return payload


async def cmd_import(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    source_indices = None
    if args.indices:
        source_indices = [int(idx.strip()) for idx in args.indices.split(",") if idx.strip()]
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.import_research_sources(
            notebook_id=notebook_id,
            task_id=args.task_id,
            source_indices=source_indices,
        )


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="Manage NotebookLM research workflows")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("start", help="Start research task")
    p.add_argument("query", help="Research query")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--source", default="web", choices=["web", "academic", "news"], help="Research source")
    p.add_argument("--mode", default="fast", choices=["fast", "deep"], help="Research depth")

    p = subparsers.add_parser("status", help="Poll latest research status")
    p.add_argument("--notebook-id", help="Notebook ID or alias")

    p = subparsers.add_parser("import", help="Import discovered sources from research task")
    p.add_argument("task_id", help="Research task ID")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--indices", help="Comma-separated source indices to import (default: all)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "start": cmd_start,
        "status": cmd_status,
        "import": cmd_import,
    }

    try:
        result = await cmd_map[args.command](args)
    except NotebookLMError as err:
        print(f"❌ [{err.code}] {err.message}", file=sys.stderr)
        if err.recovery:
            print(f"🔧 {err.recovery}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"❌ {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0



def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
