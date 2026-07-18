#!/usr/bin/env python3
"""Alias manager for nblm command shortcuts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from config import DATA_DIR

ALIASES_FILE = DATA_DIR / "aliases.json"


@dataclass
class AliasRecord:
    """Single alias mapping."""

    target: str
    object_type: str = "notebook"
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "object_type": self.object_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AliasStore:
    """Persistent alias storage backed by data/aliases.json."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or ALIASES_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.file_path.exists():
            return {"aliases": {}, "updated_at": ""}
        try:
            payload = json.loads(self.file_path.read_text())
        except Exception:
            payload = {"aliases": {}, "updated_at": ""}
        payload.setdefault("aliases", {})
        payload.setdefault("updated_at", "")
        return payload

    def _save(self) -> None:
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.file_path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    @staticmethod
    def _normalize(name: str) -> str:
        return (name or "").strip().lower()

    def list_aliases(self) -> Dict[str, AliasRecord]:
        aliases = {}
        for name, record in self._data.get("aliases", {}).items():
            aliases[name] = AliasRecord(
                target=record.get("target", ""),
                object_type=record.get("object_type", "notebook"),
                created_at=record.get("created_at", ""),
                updated_at=record.get("updated_at", ""),
            )
        return aliases

    def get(self, name: str) -> Optional[AliasRecord]:
        key = self._normalize(name)
        aliases = self._data.get("aliases", {})
        record = aliases.get(key)
        if not record:
            return None
        return AliasRecord(
            target=record.get("target", ""),
            object_type=record.get("object_type", "notebook"),
            created_at=record.get("created_at", ""),
            updated_at=record.get("updated_at", ""),
        )

    def resolve(self, value: Optional[str], object_type: Optional[str] = None) -> Optional[str]:
        if not value:
            return value
        found = self.get(value)
        if not found:
            return value
        if object_type and found.object_type != object_type:
            return value
        return found.target

    def set(self, name: str, target: str, object_type: str = "notebook") -> AliasRecord:
        key = self._normalize(name)
        now = datetime.now(timezone.utc).isoformat()
        existing = self._data["aliases"].get(key, {})
        created_at = existing.get("created_at", now)
        record = AliasRecord(
            target=target,
            object_type=object_type,
            created_at=created_at,
            updated_at=now,
        )
        self._data["aliases"][key] = record.to_dict()
        self._save()
        return record

    def delete(self, name: str) -> bool:
        key = self._normalize(name)
        if key not in self._data.get("aliases", {}):
            return False
        del self._data["aliases"][key]
        self._save()
        return True



def _print_json(payload: dict):
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage nblm aliases")
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("set", help="Set alias")
    p.add_argument("name")
    p.add_argument("target")
    p.add_argument("--type", default="notebook", choices=["notebook", "source", "artifact"])

    p = subparsers.add_parser("get", help="Get alias")
    p.add_argument("name")

    subparsers.add_parser("list", help="List aliases")

    p = subparsers.add_parser("delete", help="Delete alias")
    p.add_argument("name")

    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    store = AliasStore()

    if args.command == "set":
        record = store.set(args.name, args.target, object_type=args.type)
        payload = {"alias": args.name.lower(), **record.to_dict()}
        if args.json:
            _print_json(payload)
        else:
            print(f"✅ {args.name.lower()} -> {record.target} ({record.object_type})")
        return 0

    if args.command == "get":
        record = store.get(args.name)
        if not record:
            print(f"❌ Alias not found: {args.name}", file=sys.stderr)
            return 1
        payload = {"alias": args.name.lower(), **record.to_dict()}
        if args.json:
            _print_json(payload)
        else:
            print(f"{args.name.lower()} -> {record.target} ({record.object_type})")
        return 0

    if args.command == "list":
        aliases = store.list_aliases()
        payload = {
            "count": len(aliases),
            "aliases": {name: rec.to_dict() for name, rec in sorted(aliases.items())},
        }
        if args.json:
            _print_json(payload)
        else:
            if not aliases:
                print("No aliases configured.")
            for name, rec in sorted(aliases.items()):
                print(f"{name} -> {rec.target} ({rec.object_type})")
        return 0

    if args.command == "delete":
        deleted = store.delete(args.name)
        if not deleted:
            print(f"❌ Alias not found: {args.name}", file=sys.stderr)
            return 1
        if args.json:
            _print_json({"deleted": args.name.lower(), "success": True})
        else:
            print(f"✅ Deleted alias: {args.name.lower()}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
