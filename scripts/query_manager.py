#!/usr/bin/env python3
"""Notebook query manager with conversation and source controls."""

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


async def cmd_ask(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    source_ids = [sid.strip() for sid in args.source_ids.split(",") if sid.strip()] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        if args.goal or args.length or args.custom_prompt:
            await wrapper.configure_chat(
                notebook_id=notebook_id,
                goal=args.goal or "default",
                response_length=args.length or "default",
                custom_prompt=args.custom_prompt,
            )

        call = wrapper.query(
            notebook_id=notebook_id,
            message=args.question,
            source_ids=source_ids,
            conversation_id=args.conversation_id,
        )
        if args.timeout:
            result = await asyncio.wait_for(call, timeout=args.timeout)
        else:
            result = await call
        result["notebook_id"] = notebook_id
        return result


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="Query NotebookLM with advanced options")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("ask", help="Ask a question")
    p.add_argument("question", help="Question text")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--conversation-id", help="Conversation ID for follow-up")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    p.add_argument("--goal", choices=["default", "learning_guide", "custom"], help="Chat goal")
    p.add_argument("--length", choices=["default", "longer", "shorter"], help="Response length")
    p.add_argument("--custom-prompt", help="Custom chat prompt when goal=custom")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    try:
        result = await cmd_ask(args)
    except asyncio.TimeoutError:
        print("❌ Query timed out", file=sys.stderr)
        return 1
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
        print(result.get("text", ""))
    return 0



def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
