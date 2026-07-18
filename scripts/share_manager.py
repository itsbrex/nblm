#!/usr/bin/env python3
"""Notebook share management commands."""

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


async def cmd_status(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.get_share_status(notebook_id)


async def cmd_public(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.set_public_access(notebook_id, is_public=True)


async def cmd_private(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.set_public_access(notebook_id, is_public=False)


async def cmd_invite(args) -> dict:
    notebook_id = resolve_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.invite_collaborator(
            notebook_id=notebook_id,
            email=args.email,
            role=args.role,
            notify=not args.no_notify,
            welcome_message=args.message or "",
        )


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="Manage notebook sharing")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("status", help="Show sharing status")
    p.add_argument("--notebook-id", help="Notebook ID or alias")

    p = subparsers.add_parser("public", help="Enable public sharing")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--confirm", action="store_true", help="Confirm change")

    p = subparsers.add_parser("private", help="Disable public sharing")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--confirm", action="store_true", help="Confirm change")

    p = subparsers.add_parser("invite", help="Invite collaborator")
    p.add_argument("email", help="Collaborator email")
    p.add_argument("--notebook-id", help="Notebook ID or alias")
    p.add_argument("--role", choices=["viewer", "editor"], default="viewer")
    p.add_argument("--message", help="Welcome message")
    p.add_argument("--no-notify", action="store_true", help="Do not send notification email")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    if args.command in {"public", "private"} and not args.confirm:
        print("❌ --confirm is required for visibility changes", file=sys.stderr)
        return 1

    cmd_map = {
        "status": cmd_status,
        "public": cmd_public,
        "private": cmd_private,
        "invite": cmd_invite,
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

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0



def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
