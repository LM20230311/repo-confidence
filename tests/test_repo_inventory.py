from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "skills"
    / "repository-onboarding-coach"
    / "scripts"
    / "repo_inventory.py"
)

SPEC = importlib.util.spec_from_file_location("repo_inventory", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load inventory script: {SCRIPT_PATH}")
repo_inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repo_inventory)


class RepoInventoryTest(unittest.TestCase):
    def write(self, root: Path, relative_path: str, content: str = "") -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_inventory_for_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(
                ["git", "init", "-b", "main", str(root)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.write(root, "AGENTS.md", "# Instructions\n")
            self.write(root, "pyproject.toml", "[project]\nname='fixture'\n")
            self.write(root, "package.json", "{}\n")
            self.write(root, "app.py", "print('hello')\n")
            self.write(root, "bookmarks/urls.py", "urlpatterns = []\n")
            self.write(root, "bookmarks/tasks.py", "def refresh(): pass\n")
            self.write(root, "bookmarks/models.py", "class Bookmark: pass\n")
            self.write(root, "tests/test_app.py", "def test_app(): pass\n")
            self.write(root, "tests/resources/logo.png", "not-a-real-image\n")
            self.write(root, "migrations/001_init.sql", "select 1;\n")
            self.write(root, ".github/workflows/test.yml", "name: test\n")
            (root / ".codegraph").mkdir()

            inventory = repo_inventory.build_inventory(root)

            self.assertTrue(inventory["git"]["is_repository"])
            self.assertEqual(inventory["git"]["branch"], "main")
            self.assertTrue(inventory["capabilities"]["codegraph_index_present"])
            self.assertEqual(inventory["languages_by_file_count"]["Python"], 5)
            self.assertIn("AGENTS.md", inventory["instruction_files"])
            self.assertIn("pyproject.toml", inventory["manifests_and_build_files"])
            self.assertIn("app.py", inventory["entrypoint_candidates"])
            self.assertIn("bookmarks/urls.py", inventory["route_candidates"])
            self.assertIn("bookmarks/tasks.py", inventory["worker_candidates"])
            self.assertIn("bookmarks/models.py", inventory["persistence_candidates"])
            self.assertIn("tests/test_app.py", inventory["test_files"])
            self.assertNotIn("tests/resources/logo.png", inventory["test_files"])
            self.assertIn("migrations/001_init.sql", inventory["migration_files"])
            self.assertIn(".github/workflows/test.yml", inventory["ci_files"])
            self.assertEqual(inventory["path_counts"]["test_files"], 1)

            summary = repo_inventory.summarize_inventory(inventory, max_items=1)
            self.assertEqual(len(summary["manifests_and_build_files"]), 1)
            self.assertEqual(
                summary["truncated_lists"]["manifests_and_build_files"],
                {"shown": 1, "total": 2},
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(root),
                    "--summary",
                    "--max-items",
                    "1",
                    "--compact",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            cli_summary = json.loads(result.stdout)
            self.assertEqual(len(cli_summary["manifests_and_build_files"]), 1)
            self.assertEqual(cli_summary["path_counts"]["manifests_and_build_files"], 2)

    def test_inventory_for_non_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "main.go", "package main\n")
            self.write(root, "go.mod", "module example.test/inventory\n")
            self.write(root, "vendor/ignored.go", "package ignored\n")

            inventory = repo_inventory.build_inventory(root)

            self.assertFalse(inventory["git"]["is_repository"])
            self.assertEqual(inventory["repository"]["file_source"], "filesystem")
            self.assertEqual(inventory["languages_by_file_count"]["Go"], 1)
            self.assertIn("main.go", inventory["entrypoint_candidates"])
            self.assertIn("go.mod", inventory["manifests_and_build_files"])
            self.assertEqual(inventory["repository"]["file_count"], 2)


if __name__ == "__main__":
    unittest.main()
