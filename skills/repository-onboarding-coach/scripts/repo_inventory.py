#!/usr/bin/env python3
"""Create a read-only structural inventory for an unfamiliar repository.

The script intentionally inspects paths and Git metadata, not file contents. It is
safe to use as the first deterministic input to an AI-assisted onboarding flow.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
import subprocess
import sys


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
}

MANIFEST_NAMES = {
    "go.mod",
    "go.work",
    "package.json",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "mix.exs",
    "Package.swift",
    "CMakeLists.txt",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}

INSTRUCTION_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    ".cursorrules",
}

ENTRYPOINT_NAMES = {
    "main.go",
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "main.rs",
    "Program.cs",
    "Application.java",
    "Main.java",
    "main.rb",
    "main.php",
}

LANGUAGE_BY_SUFFIX = {
    ".go": "Go",
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cc": "C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
    ".proto": "Protocol Buffers",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".dart": "Dart",
    ".lua": "Lua",
    ".r": "R",
}


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip()


def git_file_list(root: Path) -> list[str] | None:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return sorted(
        path.decode("utf-8", errors="replace")
        for path in result.stdout.split(b"\0")
        if path
    )


def filesystem_file_list(root: Path) -> list[str]:
    files: list[str] = []
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        current = Path(current_root)
        for filename in sorted(filenames):
            path = current / filename
            try:
                files.append(path.relative_to(root).as_posix())
            except ValueError:
                continue
    return files


def is_test_file(path: str) -> bool:
    lowered = path.lower()
    name = Path(path).name.lower()
    return (
        "/test/" in f"/{lowered}"
        or "/tests/" in f"/{lowered}"
        or name.endswith("_test.go")
        or name.startswith("test_") and name.endswith(".py")
        or ".test." in name
        or ".spec." in name
        or name.endswith("test.java")
        or name.endswith("tests.cs")
    )


def is_migration_file(path: str) -> bool:
    parts = {part.lower() for part in Path(path).parts}
    return bool(parts & {"migration", "migrations", "migrate"})


def is_ci_file(path: str) -> bool:
    lowered = path.lower()
    name = Path(path).name.lower()
    return (
        lowered.startswith(".github/workflows/")
        or name in {".gitlab-ci.yml", "jenkinsfile", "circle.yml", "azure-pipelines.yml"}
        or lowered.startswith(".circleci/")
    )


def language_counts(files: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in files:
        name = Path(path).name
        if name == "Dockerfile" or name.startswith("Dockerfile."):
            counts["Dockerfile"] += 1
            continue
        language = LANGUAGE_BY_SUFFIX.get(Path(path).suffix.lower())
        if language:
            counts[language] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def top_level_entries(root: Path) -> list[str]:
    try:
        return sorted(path.name for path in root.iterdir() if path.name != ".git")
    except OSError:
        return []


def build_inventory(root: Path) -> dict[str, object]:
    git_root_raw = run_git(root, "rev-parse", "--show-toplevel")
    git_root = Path(git_root_raw).resolve() if git_root_raw else None
    files = git_file_list(root) if git_root else None
    source = "git" if files is not None else "filesystem"
    if files is None:
        files = filesystem_file_list(root)

    status = run_git(root, "status", "--porcelain=v1", "-uno") if git_root else None
    dirty_count = len(status.splitlines()) if status else 0

    instructions = [
        path
        for path in files
        if Path(path).name in INSTRUCTION_NAMES or path.endswith("/AGENTS.md")
    ]
    manifests = [path for path in files if Path(path).name in MANIFEST_NAMES]
    docs = [
        path
        for path in files
        if Path(path).name.lower().startswith("readme")
        or path.lower().startswith("docs/")
        or "/docs/" in path.lower()
    ]
    entrypoints = [
        path
        for path in files
        if Path(path).name in ENTRYPOINT_NAMES
        or path.startswith("cmd/") and Path(path).name.endswith((".go", ".py", ".rs"))
        or path.startswith("bin/")
    ]
    tests = [path for path in files if is_test_file(path)]
    migrations = [path for path in files if is_migration_file(path)]
    ci_files = [path for path in files if is_ci_file(path)]

    return {
        "repository": {
            "requested_path": str(root),
            "resolved_path": str(root.resolve()),
            "file_source": source,
            "file_count": len(files),
            "top_level_entries": top_level_entries(root),
        },
        "git": {
            "is_repository": git_root is not None,
            "root": str(git_root) if git_root else None,
            "head": run_git(root, "rev-parse", "HEAD") if git_root else None,
            "branch": run_git(root, "branch", "--show-current") if git_root else None,
            "dirty_tracked_file_count": dirty_count,
        },
        "capabilities": {
            "codegraph_index_present": (root / ".codegraph").is_dir(),
        },
        "languages_by_file_count": language_counts(files),
        "instruction_files": sorted(instructions),
        "manifests_and_build_files": sorted(manifests),
        "entrypoint_candidates": sorted(entrypoints),
        "test_files": sorted(tests),
        "migration_files": sorted(migrations),
        "ci_files": sorted(ci_files),
        "documentation_candidates": sorted(docs),
        "notes": [
            "This inventory is structural and does not prove runtime behavior.",
            "Inspect repository instructions before reading or changing code.",
            "Use CodeGraph first when codegraph_index_present is true and local policy requires it.",
            "Treat entrypoints as candidates until verified from build or runtime configuration.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only structural inventory for a repository."
    )
    parser.add_argument(
        "repository",
        nargs="?",
        default=".",
        help="Path to the repository or directory to inspect (default: current directory)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repository).expanduser()
    if not root.is_dir():
        print(f"error: repository path is not a directory: {root}", file=sys.stderr)
        return 2

    inventory = build_inventory(root)
    if args.compact:
        print(json.dumps(inventory, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
