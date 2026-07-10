from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
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
            self.write(root, "app.py", "print('hello')\n")
            self.write(root, "tests/test_app.py", "def test_app(): pass\n")
            self.write(root, "migrations/001_init.sql", "select 1;\n")
            self.write(root, ".github/workflows/test.yml", "name: test\n")
            (root / ".codegraph").mkdir()

            inventory = repo_inventory.build_inventory(root)

            self.assertTrue(inventory["git"]["is_repository"])
            self.assertEqual(inventory["git"]["branch"], "main")
            self.assertTrue(inventory["capabilities"]["codegraph_index_present"])
            self.assertEqual(inventory["languages_by_file_count"]["Python"], 2)
            self.assertIn("AGENTS.md", inventory["instruction_files"])
            self.assertIn("pyproject.toml", inventory["manifests_and_build_files"])
            self.assertIn("app.py", inventory["entrypoint_candidates"])
            self.assertIn("tests/test_app.py", inventory["test_files"])
            self.assertIn("migrations/001_init.sql", inventory["migration_files"])
            self.assertIn(".github/workflows/test.yml", inventory["ci_files"])

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
