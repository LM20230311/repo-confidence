from __future__ import annotations

import importlib.util
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
    / "atlas_freshness.py"
)

SPEC = importlib.util.spec_from_file_location("atlas_freshness", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load freshness script: {SCRIPT_PATH}")
atlas_freshness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas_freshness)


class AtlasFreshnessTest(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def write(self, root: Path, relative_path: str, content: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def init_repository(self, root: Path) -> None:
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Repo Confidence Test")
        self.git(root, "config", "user.email", "test@example.invalid")

    def commit_all(self, root: Path, message: str) -> str:
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", message)
        return self.git(root, "rev-parse", "HEAD")

    def atlas_page(self, commit: str, evidence: str | None = None) -> str:
        evidence_line = f"> Evidence paths: `{evidence}`\n" if evidence else ""
        return (
            "# Flow\n\n"
            "> Status: Verified\n"
            f"> Last verified commit: `{commit}`\n"
            f"{evidence_line}"
            "> Known gaps: None known\n"
        )

    def test_current_when_page_targets_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_repository(root)
            self.write(root, "src/app.py", "print('v1')\n")
            head = self.commit_all(root, "initial code")
            self.write(root, "docs/project-atlas/flow.md", self.atlas_page(head, "src/app.py"))

            report = atlas_freshness.build_report(root, "docs/project-atlas")

            self.assertEqual(report["summary"], {"current": 1})
            self.assertFalse(report["needs_review"])

    def test_unchanged_and_changed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_repository(root)
            self.write(root, "src/app.py", "print('v1')\n")
            verified = self.commit_all(root, "initial code")
            self.write(root, "docs/project-atlas/flow.md", self.atlas_page(verified, "src/app.py"))
            self.commit_all(root, "add atlas")

            report = atlas_freshness.build_report(root, "docs/project-atlas")
            self.assertEqual(report["summary"], {"unchanged_evidence": 1})
            self.assertFalse(report["needs_review"])

            self.write(root, "src/app.py", "print('v2')\n")
            self.commit_all(root, "change evidence")
            report = atlas_freshness.build_report(root, "docs/project-atlas")

            self.assertEqual(report["summary"], {"review": 1})
            self.assertTrue(report["needs_review"])
            self.assertEqual(report["pages"][0]["changed_evidence_paths"], ["src/app.py"])

    def test_unmapped_page_requires_review_after_head_advances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_repository(root)
            self.write(root, "src/app.py", "print('v1')\n")
            verified = self.commit_all(root, "initial code")
            self.write(root, "docs/project-atlas/flow.md", self.atlas_page(verified))
            self.commit_all(root, "add atlas")

            report = atlas_freshness.build_report(root, "docs/project-atlas")

            self.assertEqual(report["summary"], {"unmapped": 1})
            self.assertTrue(report["needs_review"])

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(root), "--strict"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(result.returncode, 1)

    def test_external_verification_commit_is_reported_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_repository(root)
            external_sha = "4e570389dd433a717373ce9c9b822b59f5ed3d5d"
            page = (
                "# External case\n\n"
                "> Status: Partially verified\n"
                "> Last verified commit: "
                f"[`4e570389`](https://github.com/QuantumNous/new-api/tree/{external_sha})\n"
            )
            self.write(root, "docs/project-atlas/index.md", page)
            self.commit_all(root, "external atlas")

            report = atlas_freshness.build_report(root, "docs/project-atlas")

            self.assertEqual(report["summary"], {"external": 1})
            self.assertFalse(report["needs_review"])


if __name__ == "__main__":
    unittest.main()
