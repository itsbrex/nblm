#!/usr/bin/env python3
"""Artifact export manager (Docs/Sheets)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from notebooklm_wrapper import NotebookLMError, NotebookLMWrapper
from artifact_manager import get_notebook_id


async def cmd_create(args) -> dict:
    notebook_id = get_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        return await wrapper.export_artifact(
            notebook_id=notebook_id,
            artifact_id=args.artifact_id,
            export_type=args.type,
            title=args.title,
        )


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="Export NotebookLM artifacts to Google Docs/Sheets")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("create", help="Export an artifact")
    p.add_argument("artifact_id", help="Artifact ID")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--type", choices=["docs", "sheets"], default="docs", help="Export destination")
    p.add_argument("--title", default="NotebookLM Export", help="Export title")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    try:
        result = await cmd_create(args)
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
