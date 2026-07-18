#!/usr/bin/env python3
"""Compatibility setup manager exposing add/remove/list commands."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import init_platform


def _resolve_target(target: str | None) -> Path:
    return Path(target).resolve() if target else Path.cwd().resolve()


def cmd_list() -> int:
    print("Supported setup targets:")
    for key, cfg in init_platform.PLATFORMS.items():
        print(f"- {key}: {cfg['description']}")
    return 0


def cmd_add(platform: str, target: Path, force: bool) -> int:
    ok = init_platform.init_platform(platform=platform, target_dir=target, force=force)
    return 0 if ok else 1


def cmd_remove(platform: str, target: Path) -> int:
    platforms = list(init_platform.PLATFORMS.keys()) if platform == "all" else [platform]
    for key in platforms:
        if key not in init_platform.PLATFORMS:
            print(f"❌ Unknown platform: {key}")
            return 1
        cfg = init_platform.PLATFORMS[key]
        skill_file = target / cfg["root"] / cfg["skill_path"] / cfg["filename"]
        if skill_file.exists():
            skill_file.unlink()
            print(f"✅ Removed: {skill_file}")
            parent = skill_file.parent
            try:
                if not any(parent.iterdir()):
                    parent.rmdir()
            except Exception:
                pass
        else:
            print(f"ℹ️ Not found: {skill_file}")

        symlink_rel = cfg.get("symlink_path")
        if symlink_rel and sys.platform != "win32":
            symlink_path = Path.home() / symlink_rel
            if symlink_path.exists() or symlink_path.is_symlink():
                if symlink_path.is_symlink() or symlink_path.is_file():
                    symlink_path.unlink()
                else:
                    shutil.rmtree(symlink_path)
                print(f"✅ Removed symlink/path: {symlink_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage nblm setup integrations")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("add", help="Install setup files for platform")
    p.add_argument("platform", choices=[*init_platform.PLATFORMS.keys(), "all"])
    p.add_argument("--target-dir", help="Target project directory")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")

    p = subparsers.add_parser("remove", help="Remove setup files for platform")
    p.add_argument("platform", choices=[*init_platform.PLATFORMS.keys(), "all"])
    p.add_argument("--target-dir", help="Target project directory")

    subparsers.add_parser("list", help="List supported setup targets")

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list()
    if args.command == "add":
        return cmd_add(args.platform, _resolve_target(args.target_dir), force=args.force)
    if args.command == "remove":
        return cmd_remove(args.platform, _resolve_target(args.target_dir))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
