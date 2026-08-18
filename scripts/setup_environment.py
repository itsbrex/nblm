#!/usr/bin/env python3
"""
Environment setup for nblm using uv.
Manages virtual environment and dependencies automatically.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _get_npm_command():
    """Get the npm command for the current platform."""
    if os.name == "nt":
        return "npm.cmd"
    return "npm"


def _get_uv_command():
    """Get the uv command for the current platform."""
    if os.name == "nt":
        return "uv.exe"
    return "uv"


class SkillEnvironment:
    """Manages skill-specific environment with uv."""

    def __init__(self):
        self.skill_dir = Path(__file__).parent.parent
        self.venv_dir = self.skill_dir / ".venv"
        self.pyproject_file = self.skill_dir / "pyproject.toml"
        self.lock_file = self.skill_dir / "uv.lock"

        if os.name == "nt":
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"

    def ensure_uv(self) -> bool:
        """Ensure uv is installed and available."""
        uv_cmd = _get_uv_command()
        if shutil.which(uv_cmd):
            return True
        print("❌ uv is required but was not found in PATH")
        print("   Install uv: https://docs.astral.sh/uv/getting-started/installation/")
        return False

    def ensure_venv(self) -> bool:
        """Ensure virtual environment exists and is set up with uv."""
        if not self.ensure_uv():
            return False

        if self.is_in_skill_venv():
            print("✅ Already running in skill virtual environment")
            return True

        if self.venv_python.exists():
            return True

        print(f"🔧 Creating virtual environment in {self.venv_dir.name}/ with uv")
        try:
            subprocess.run(
                [_get_uv_command(), "venv", str(self.venv_dir)],
                cwd=str(self.skill_dir),
                check=True,
            )
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create venv: {e}")
            return False

    def ensure_python_deps(self) -> bool:
        """Install/update Python dependencies via uv."""
        if not self.ensure_uv():
            return False

        if self.pyproject_file.exists():
            print("📦 Syncing Python dependencies with uv...")
            cmd = [_get_uv_command(), "sync", "--python", str(self.venv_python)]
            if self.lock_file.exists():
                cmd.insert(2, "--frozen")
            try:
                subprocess.run(cmd, cwd=str(self.skill_dir), check=True)
                print("✅ Python dependencies synced")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to sync dependencies: {e}")
                return False

        print("❌ pyproject.toml not found; cannot sync Python dependencies with uv")
        return False

    def ensure_node_deps(self) -> bool:
        """Ensure Node.js dependencies are installed."""
        package_json = self.skill_dir / "package.json"
        node_modules = self.skill_dir / "node_modules"
        if not package_json.exists():
            return True
        if node_modules.exists():
            return True

        print("📦 Installing Node.js dependencies...")
        npm_cmd = _get_npm_command()
        try:
            subprocess.run(
                [npm_cmd, "install"],
                check=True,
                cwd=str(self.skill_dir),
            )
            print("✅ Node.js dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: npm install failed: {e}")
            print("   Ensure Node.js and npm are installed")
            return False

        try:
            subprocess.run(
                [npm_cmd, "run", "install-browsers"],
                check=True,
                cwd=str(self.skill_dir),
            )
            print("✅ Playwright browsers installed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: browser install failed: {e}")
            print("   You may need to run manually: npm run install-browsers")
        return True

    def ensure_environment(self) -> bool:
        """Ensure the full environment is ready."""
        if not self.ensure_venv():
            return False
        if not self.ensure_python_deps():
            return False
        if not self.ensure_node_deps():
            return False
        return True

    def is_in_skill_venv(self) -> bool:
        """Check if we're already running in the skill's venv."""
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )
        if not in_venv:
            return False
        return Path(sys.prefix) == self.venv_dir

    def get_python_executable(self) -> str:
        """Get the correct Python executable to use."""
        if self.venv_python.exists():
            return str(self.venv_python)
        return sys.executable

    def run_script(self, script_name: str, args: list = None) -> int:
        """Run a script with the virtual environment."""
        script_path = self.skill_dir / "scripts" / script_name
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return 1

        if not self.ensure_environment():
            print("❌ Failed to set up environment")
            return 1

        cmd = [str(self.venv_python), str(script_path)]
        if args:
            cmd.extend(args)

        print(f"🚀 Running: {script_name} with venv Python")
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            print(f"❌ Failed to run script: {e}")
            return 1

    def activate_instructions(self) -> str:
        """Get instructions for manual activation."""
        if os.name == "nt":
            activate = self.venv_dir / "Scripts" / "activate.bat"
            return f"Run: {activate}"
        activate = self.venv_dir / "bin" / "activate"
        return f"Run: source {activate}"

    def manual_setup_instructions(self) -> str:
        """Get manual setup instructions."""
        if os.name == "nt":
            return "\n".join(
                [
                    "uv venv .venv",
                    ".\\.venv\\Scripts\\activate",
                    "uv sync",
                    "npm install",
                    "npm run install-browsers",
                ]
            )
        return "\n".join(
            [
                "uv venv .venv",
                "source .venv/bin/activate",
                "uv sync",
                "npm install",
                "npm run install-browsers",
            ]
        )


def main():
    """Main entry point for environment setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup NotebookLM skill environment")
    parser.add_argument("--check", action="store_true", help="Check if environment is set up")
    parser.add_argument("--run", help="Run a script with the venv (e.g., --run ask_question.py)")
    parser.add_argument("args", nargs="*", help="Arguments to pass to the script")
    args = parser.parse_args()

    env = SkillEnvironment()

    if args.check:
        if env.venv_dir.exists():
            print(f"✅ Virtual environment exists: {env.venv_dir}")
            print(f"   Python: {env.get_python_executable()}")
            print(f"   To activate manually: {env.activate_instructions()}")
        else:
            print("❌ No virtual environment found")
            print("   Manual setup:")
            print(env.manual_setup_instructions())
        return

    if args.run:
        return env.run_script(args.run, args.args)

    if env.ensure_environment():
        print("\n✅ Environment ready!")
        print(f"   Virtual env: {env.venv_dir}")
        print(f"   Python: {env.get_python_executable()}")
        print(f"\nTo activate manually: {env.activate_instructions()}")
    else:
        print("\n❌ Environment setup failed")
        print("Manual setup:")
        print(env.manual_setup_instructions())
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
