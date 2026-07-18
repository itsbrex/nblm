#!/usr/bin/env python3
"""Skill lifecycle manager for nblm platform integrations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import init_platform
import setup_manager


def _skill_path() -> Path:
    return (Path(__file__).parent.parent / "SKILL.md").resolve()


def cmd_list(json_output: bool = False) -> int:
    platforms = {
        key: {
            "name": cfg["name"],
            "description": cfg["description"],
            "root": cfg["root"],
        }
        for key, cfg in init_platform.PLATFORMS.items()
    }
    if json_output:
        print(json.dumps({"platforms": platforms}, indent=2, ensure_ascii=False))
    else:
        print("Supported tools:")
        for key, cfg in sorted(platforms.items()):
            print(f"- {key}: {cfg['description']}")
    return 0


def cmd_show(json_output: bool = False) -> int:
    skill_file = _skill_path()
    if json_output:
        print(json.dumps({"skill_file": str(skill_file)}, indent=2, ensure_ascii=False))
    else:
        print(skill_file)
    return 0


def cmd_install(tool: str, target_dir: str | None, force: bool, json_output: bool = False) -> int:
    rc = setup_manager.cmd_add(tool, setup_manager._resolve_target(target_dir), force=force)
    if json_output:
        print(json.dumps({"tool": tool, "installed": rc == 0}, indent=2, ensure_ascii=False))
    return rc


def cmd_uninstall(tool: str, target_dir: str | None, json_output: bool = False) -> int:
    rc = setup_manager.cmd_remove(tool, setup_manager._resolve_target(target_dir))
    if json_output:
        print(json.dumps({"tool": tool, "uninstalled": rc == 0}, indent=2, ensure_ascii=False))
    return rc


def cmd_update(tool: str, target_dir: str | None, json_output: bool = False) -> int:
    rc = setup_manager.cmd_add(tool, setup_manager._resolve_target(target_dir), force=True)
    if json_output:
        print(json.dumps({"tool": tool, "updated": rc == 0}, indent=2, ensure_ascii=False))
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage nblm skill installation")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("install", help="Install skill files for a tool")
    p.add_argument("tool", choices=[*init_platform.PLATFORMS.keys(), "all"])
    p.add_argument("--target-dir")
    p.add_argument("--force", action="store_true")

    p = subparsers.add_parser("uninstall", help="Uninstall skill files for a tool")
    p.add_argument("tool", choices=[*init_platform.PLATFORMS.keys(), "all"])
    p.add_argument("--target-dir")

    p = subparsers.add_parser("update", help="Update skill files for a tool")
    p.add_argument("tool", choices=[*init_platform.PLATFORMS.keys(), "all"])
    p.add_argument("--target-dir")

    subparsers.add_parser("list", help="List available tools")
    subparsers.add_parser("show", help="Show skill file path")

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(json_output=args.json)
    if args.command == "show":
        return cmd_show(json_output=args.json)
    if args.command == "install":
        return cmd_install(args.tool, args.target_dir, args.force, json_output=args.json)
    if args.command == "uninstall":
        return cmd_uninstall(args.tool, args.target_dir, json_output=args.json)
    if args.command == "update":
        return cmd_update(args.tool, args.target_dir, json_output=args.json)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
