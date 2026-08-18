import unittest
from unittest import mock
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "scripts"))
sys.path.insert(0, str(repo_root))

import scripts.nblm_cli as nblm_cli


class NblmCliRoutingTests(unittest.TestCase):
    def test_normalize_flat_alias(self):
        self.assertEqual(
            nblm_cli.normalize_command(["upload-url", "https://example.com"]),
            ["source", "add", "--url", "https://example.com"],
        )

    def test_normalize_legacy_ask_alias(self):
        self.assertEqual(
            nblm_cli.normalize_command(["ask", "What is new?"]),
            ["query", "ask", "What is new?"],
        )

    def test_normalize_legacy_podcast_alias(self):
        self.assertEqual(
            nblm_cli.normalize_command(["podcast", "--wait"]),
            ["audio", "create", "--wait"],
        )

    def test_normalize_legacy_source_refresh_alias(self):
        self.assertEqual(
            nblm_cli.normalize_command(["source-refresh", "src-1"]),
            ["source", "sync", "src-1"],
        )

    def test_normalize_verb_alias(self):
        self.assertEqual(
            nblm_cli.normalize_command(["create", "report", "--wait"]),
            ["report", "create", "--wait"],
        )

    def test_normalize_legacy_notebook_create(self):
        self.assertEqual(
            nblm_cli.normalize_command(["create", "My Notebook"]),
            ["notebook", "create", "My Notebook"],
        )

    def test_normalize_legacy_sync_folder(self):
        self.assertEqual(
            nblm_cli.normalize_command(["sync", "./docs"]),
            ["source", "sync-folder", "./docs"],
        )

    def test_translate_artifact_group_create(self):
        self.assertEqual(
            nblm_cli._translate_artifact_group("report", ["create", "--wait"]),
            ["generate-report", "--wait"],
        )

    def test_translate_artifact_group_status_positional(self):
        self.assertEqual(
            nblm_cli._translate_artifact_group("audio", ["status", "task-1"]),
            ["status", "--task-id", "task-1"],
        )

    def test_handle_download_translates_type(self):
        with mock.patch.object(nblm_cli, "_with_module_argv", return_value=0) as patched:
            rc = nblm_cli.handle_download(["slides", "deck.pdf", "--artifact-id", "a1"])
        self.assertEqual(rc, 0)
        patched.assert_called_once()
        called_args = patched.call_args.args[1]
        self.assertEqual(called_args[0], "download")
        self.assertIn("--type", called_args)
        self.assertIn("slide-deck", called_args)


if __name__ == "__main__":
    unittest.main()
