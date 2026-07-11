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
    / "evidence_manifest.py"
)

SPEC = importlib.util.spec_from_file_location("evidence_manifest", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load evidence manifest script: {SCRIPT_PATH}")
evidence_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence_manifest)


class EvidenceManifestTest(unittest.TestCase):
    def write(self, root: Path, relative_path: str, content: str = "") -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_extracts_django_routes_tasks_models_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(
                ["git", "init", "-b", "main", str(root)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.write(root, "manage.py", "def main(): pass\n")
            self.write(
                root,
                "bookmarks/urls.py",
                """from django.urls import path
from . import views

urlpatterns = [
    path("bookmarks/", views.list_bookmarks, name="bookmark-list"),
]
""",
            )
            self.write(
                root,
                "bookmarks/api/routes.py",
                """from rest_framework.routers import SimpleRouter
from .views import BookmarkViewSet

router = SimpleRouter()
router.register("", BookmarkViewSet, basename="bookmark")
""",
            )
            self.write(
                root,
                "bookmarks/tasks.py",
                """from huey.contrib.djhuey import task

@task()
def refresh_bookmark(bookmark_id: int):
    return bookmark_id
""",
            )
            self.write(
                root,
                "bookmarks/models.py",
                """from django.db import models

class Bookmark(models.Model):
    title = models.CharField(max_length=100)
""",
            )
            self.write(
                root,
                "bookmarks/tests/test_bookmarks_api.py",
                "def test_bookmark_list(): pass\n",
            )
            self.write(
                root,
                "bookmarks/tests/test_bookmarks_tasks.py",
                "def test_refresh_bookmark(): pass\n",
            )
            self.write(
                root,
                "bookmarks/migrations/0001_initial.py",
                "class Migration: pass\n",
            )

            manifest = evidence_manifest.build_manifest(root)

            self.assertEqual(manifest["schema_version"], "1.0")
            self.assertEqual(manifest["semantic_counts"]["route_registrations"], 2)
            self.assertEqual(manifest["semantic_counts"]["task_registrations"], 1)
            self.assertEqual(manifest["semantic_counts"]["model_classes"], 1)

            by_path = {item["path"]: item for item in manifest["evidence"]}
            django_route = by_path["bookmarks/urls.py"]["python"][
                "route_registrations"
            ][0]
            self.assertEqual(django_route["route"], "bookmarks/")
            self.assertEqual(django_route["handler"], "views.list_bookmarks")

            router = by_path["bookmarks/api/routes.py"]["python"][
                "route_registrations"
            ][0]
            self.assertEqual(router["style"], "router.register")
            self.assertEqual(router["handler"], "BookmarkViewSet")
            self.assertTrue(
                any(
                    flow["title"] == "<root route> -> BookmarkViewSet"
                    for flow in manifest["flow_candidates"]
                )
            )

            tasks = by_path["bookmarks/tasks.py"]["python"]["task_registrations"]
            self.assertEqual(tasks[0]["symbol"], "refresh_bookmark")
            models = by_path["bookmarks/models.py"]["python"]["model_classes"]
            self.assertEqual(models[0]["symbol"], "Bookmark")

            task_relations = by_path["bookmarks/tasks.py"]["relations"]
            self.assertIn(
                "bookmarks/tests/test_bookmarks_tasks.py",
                task_relations["tests"]["paths"],
            )
            self.assertEqual(task_relations["tests"]["status"], "heuristic_candidate")
            self.assertIn(
                "bookmarks/migrations/0001_initial.py",
                by_path["bookmarks/models.py"]["relations"]["migrations"]["paths"],
            )
            self.assertTrue(
                all(
                    flow["status"] == "candidate_not_verified_call_graph"
                    for flow in manifest["flow_candidates"]
                )
            )

    def test_summary_and_non_python_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "go.mod", "module example.test/manifest\n")
            self.write(root, "cmd/server/main.go", "package main\n")
            self.write(root, "internal/routes.go", "package internal\n")

            manifest = evidence_manifest.build_manifest(root)
            by_path = {item["path"]: item for item in manifest["evidence"]}
            self.assertEqual(
                by_path["internal/routes.go"]["python"]["parse_status"],
                "semantic_parser_not_available",
            )
            self.assertEqual(manifest["semantic_counts"]["flow_candidates"], 0)

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
            summary = json.loads(result.stdout)
            self.assertEqual(len(summary["evidence"]), 1)
            self.assertEqual(
                summary["truncated_lists"]["evidence"], {"shown": 1, "total": 2}
            )

    def test_manifest_does_not_emit_source_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            secret = "SHOULD_NOT_APPEAR_IN_MANIFEST"
            self.write(
                root,
                "app/urls.py",
                f"SECRET = '{secret}'\nurlpatterns = []\n",
            )

            serialized = json.dumps(evidence_manifest.build_manifest(root))
            self.assertNotIn(secret, serialized)


if __name__ == "__main__":
    unittest.main()
