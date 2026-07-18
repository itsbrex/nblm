import tempfile
import unittest
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "scripts"))
sys.path.insert(0, str(repo_root))

import scripts.alias_manager as alias_manager
import scripts.config_manager as config_manager


class AliasManagerTests(unittest.TestCase):
    def test_set_get_list_delete_alias(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = alias_manager.AliasStore(file_path=Path(tmpdir) / "aliases.json")

            rec = store.set("prod", "notebook-123", object_type="notebook")
            self.assertEqual(rec.target, "notebook-123")

            fetched = store.get("PROD")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.target, "notebook-123")

            aliases = store.list_aliases()
            self.assertIn("prod", aliases)

            resolved = store.resolve("prod", object_type="notebook")
            self.assertEqual(resolved, "notebook-123")

            deleted = store.delete("prod")
            self.assertTrue(deleted)
            self.assertIsNone(store.get("prod"))


class ConfigManagerTests(unittest.TestCase):
    def test_set_get_nested_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = config_manager.ConfigStore(file_path=Path(tmpdir) / "config.json")
            store.set("defaults.language", "fr")
            self.assertEqual(store.get("defaults.language"), "fr")
            self.assertIsNone(store.get("defaults.missing"))

    def test_parse_value(self):
        self.assertEqual(config_manager._parse_value("true"), True)
        self.assertEqual(config_manager._parse_value("false"), False)
        self.assertEqual(config_manager._parse_value("null"), None)
        self.assertEqual(config_manager._parse_value("42"), 42)
        self.assertEqual(config_manager._parse_value("3.14"), 3.14)
        self.assertEqual(config_manager._parse_value("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
