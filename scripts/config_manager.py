#!/usr/bin/env python3
"""User config manager for nblm."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config import DATA_DIR

CONFIG_FILE = DATA_DIR / "config.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    "output": {
        "json": False,
        "quiet": False,
    },
    "defaults": {
        "notebook_id": None,
        "audio_format": "DEEP_DIVE",
        "audio_length": "DEFAULT",
        "language": "en",
    },
    "updated_at": "",
}


class ConfigStore:
    """Persistent config storage backed by data/config.json."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or CONFIG_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return json.loads(json.dumps(DEFAULT_CONFIG))
        try:
            loaded = json.loads(self.file_path.read_text())
        except Exception:
            loaded = {}
        merged = json.loads(json.dumps(DEFAULT_CONFIG))
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def save(self) -> None:
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.file_path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def get(self, key_path: str, default: Any = None) -> Any:
        current: Any = self._data
        for part in key_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, key_path: str, value: Any) -> None:
        parts = key_path.split(".")
        current: Dict[str, Any] = self._data
        for part in parts[:-1]:
            next_value = current.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                current[part] = next_value
            current = next_value
        current[parts[-1]] = value
        self.save()



def _parse_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw



def main() -> int:
    parser = argparse.ArgumentParser(description="Manage nblm user config")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("show", help="Show full config")

    p = subparsers.add_parser("get", help="Get config value")
    p.add_argument("key", help="Dot path key, e.g. defaults.language")

    p = subparsers.add_parser("set", help="Set config value")
    p.add_argument("key", help="Dot path key, e.g. defaults.language")
    p.add_argument("value", help="Value to set")

    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    store = ConfigStore()

    if args.command == "show":
        print(json.dumps(store.data, indent=2, ensure_ascii=False))
        return 0

    if args.command == "get":
        value = store.get(args.key)
        if value is None:
            print(f"❌ Config key not found: {args.key}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"key": args.key, "value": value}, indent=2, ensure_ascii=False))
        else:
            if isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2, ensure_ascii=False))
            else:
                print(value)
        return 0

    if args.command == "set":
        value = _parse_value(args.value)
        store.set(args.key, value)
        if args.json:
            print(json.dumps({"key": args.key, "value": value, "success": True}, indent=2, ensure_ascii=False))
        else:
            print(f"✅ Set {args.key} = {value}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
