#!/usr/bin/env python3
"""Diagnostic checks for nblm runtime, auth, and local data."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

from auth_manager import AuthManager, get_watchdog_status
from config import DATA_DIR, AUTH_DIR
from notebook_manager import NotebookLibrary


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }


class Doctor:
    """Runs health checks for local nblm installation."""

    def __init__(self):
        self.auth = AuthManager()
        self.library = NotebookLibrary()

    def run(self) -> List[CheckResult]:
        checks: List[Callable[[], CheckResult]] = [
            self.check_uv,
            self.check_node,
            self.check_npm,
            self.check_data_dir,
            self.check_auth_dir,
            self.check_google_auth,
            self.check_notebook_library,
            self.check_active_notebook,
            self.check_browser_daemon,
        ]
        return [check() for check in checks]

    @staticmethod
    def _exists(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    def check_uv(self) -> CheckResult:
        return CheckResult("uv", "pass" if self._exists("uv") else "fail", "uv command availability")

    def check_node(self) -> CheckResult:
        return CheckResult("node", "pass" if self._exists("node") else "warn", "Node.js runtime")

    def check_npm(self) -> CheckResult:
        return CheckResult("npm", "pass" if self._exists("npm") else "warn", "npm package manager")

    def check_data_dir(self) -> CheckResult:
        exists = DATA_DIR.exists() and DATA_DIR.is_dir()
        return CheckResult("data_dir", "pass" if exists else "warn", str(DATA_DIR))

    def check_auth_dir(self) -> CheckResult:
        exists = AUTH_DIR.exists() and AUTH_DIR.is_dir()
        return CheckResult("auth_dir", "pass" if exists else "warn", str(AUTH_DIR))

    def check_google_auth(self) -> CheckResult:
        info = self.auth.get_auth_info("google")
        if info.get("authenticated"):
            return CheckResult("google_auth", "pass", f"Authenticated since {info.get('timestamp', 'unknown')}")
        return CheckResult("google_auth", "warn", "Not authenticated; run auth_manager.py setup")

    def check_notebook_library(self) -> CheckResult:
        count = len(self.library.list_notebooks())
        if count > 0:
            return CheckResult("library", "pass", f"{count} notebook(s) in library")
        return CheckResult("library", "warn", "No notebooks in local library")

    def check_active_notebook(self) -> CheckResult:
        active = self.library.get_active_notebook()
        if active:
            return CheckResult("active_notebook", "pass", active.get("name") or active.get("id") or "unknown")
        return CheckResult("active_notebook", "warn", "No active notebook configured")

    def check_browser_daemon(self) -> CheckResult:
        try:
            status = get_watchdog_status()
            if status.get("daemon_running"):
                return CheckResult("browser_daemon", "pass", "Agent-browser daemon running")
            return CheckResult("browser_daemon", "warn", "Agent-browser daemon not running")
        except Exception:
            return CheckResult("browser_daemon", "warn", "Unable to inspect watchdog state")



def _summary(results: List[CheckResult]) -> Dict[str, int]:
    summary: Dict[str, int] = {"pass": 0, "warn": 0, "fail": 0}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run nblm diagnostic checks")
    parser.add_argument("--json", action="store_true", help="Output diagnostics as JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings")
    args = parser.parse_args()

    doctor = Doctor()
    results = doctor.run()
    summary = _summary(results)

    if args.json:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "checks": [check.to_dict() for check in results],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print("nblm doctor")
        print("=" * 40)
        for result in results:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(result.status, "•")
            print(f"{icon} {result.name}: {result.detail}")
        print("-" * 40)
        print(f"pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}")

    if summary["fail"] > 0:
        return 1
    if args.strict and summary["warn"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
