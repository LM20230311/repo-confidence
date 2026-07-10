#!/usr/bin/env python3
"""Report whether Project Atlas pages may be stale relative to Git HEAD.

The checker is read-only. It relies on explicit verification commits and
machine-readable evidence paths instead of guessing business dependencies.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


COMMIT_LABELS = (
    "Last verified commit",
    "Last reviewed commit",
    "Prepared against commit",
    "最近验证提交",
    "最近检查提交",
    "分析提交",
)
EVIDENCE_PATH_LABELS = ("Evidence paths", "证据路径")
SHA_RE = re.compile(r"(?<![0-9a-f])([0-9a-f]{7,40})(?![0-9a-f])", re.IGNORECASE)
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
URL_RE = re.compile(r"\((https?://[^)]+)\)")

REVIEW_STATUSES = {"review", "diverged", "unmapped", "unverified", "unknown_commit"}
STATUS_LABELS = {
    "en": {
        "current": "current",
        "unchanged_evidence": "evidence unchanged",
        "review": "review required",
        "diverged": "history diverged",
        "unmapped": "evidence unmapped",
        "unverified": "unverified",
        "unknown_commit": "unknown commit",
        "external": "external reference",
    },
    "zh": {
        "current": "当前",
        "unchanged_evidence": "证据路径未变化",
        "review": "需要复核",
        "diverged": "提交历史已分叉",
        "unmapped": "未声明证据路径",
        "unverified": "尚未验证",
        "unknown_commit": "无法识别验证提交",
        "external": "外部仓库证据",
    },
}


def run_git(root: Path, *args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return result.returncode, result.stdout.strip()


def git_root(path: Path) -> Path | None:
    code, output = run_git(path, "rev-parse", "--show-toplevel")
    if code != 0 or not output:
        return None
    return Path(output).resolve()


def metadata_value(line: str, labels: Iterable[str]) -> str | None:
    stripped = line.strip()
    if not stripped.startswith(">"):
        return None
    body = stripped[1:].strip()
    for label in labels:
        match = re.match(rf"^{re.escape(label)}\s*[:：]\s*(.*)$", body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_commit(value: str | None) -> tuple[str | None, str | None]:
    if not value or "<git-sha>" in value:
        return None, None
    sha_match = SHA_RE.search(value)
    url_match = URL_RE.search(value)
    return (
        sha_match.group(1).lower() if sha_match else None,
        url_match.group(1) if url_match else None,
    )


def looks_like_path(value: str) -> bool:
    if not value or value.startswith(("http://", "https://")):
        return False
    if value.startswith("<") and value.endswith(">"):
        return False
    path = Path(value)
    return "/" in value or path.suffix != "" or value.startswith(".")


def normalize_evidence_path(value: str) -> str | None:
    candidate = value.strip().strip("'\"").split("#", 1)[0].strip()
    if not candidate:
        return None
    if ":" in candidate:
        path_part, _symbol = candidate.split(":", 1)
        if looks_like_path(path_part):
            candidate = path_part
    candidate = candidate.removeprefix("./")
    if not looks_like_path(candidate):
        return None
    return Path(candidate).as_posix()


def extract_evidence_paths(value: str | None) -> list[str]:
    if not value:
        return []
    tokens = CODE_SPAN_RE.findall(value)
    if not tokens:
        tokens = re.split(r"[,，]", value)
    paths = {
        normalized
        for token in tokens
        if (normalized := normalize_evidence_path(token)) is not None
    }
    return sorted(paths)


def parse_page(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    commit_value: str | None = None
    evidence_value: str | None = None
    for line in text.splitlines():
        if commit_value is None:
            commit_value = metadata_value(line, COMMIT_LABELS)
        if evidence_value is None:
            evidence_value = metadata_value(line, EVIDENCE_PATH_LABELS)
        if commit_value is not None and evidence_value is not None:
            break
    commit, commit_url = extract_commit(commit_value)
    return {
        "commit": commit,
        "commit_url": commit_url,
        "evidence_paths": extract_evidence_paths(evidence_value),
    }


def commit_exists(root: Path, commit: str) -> bool:
    code, _ = run_git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    return code == 0


def analyze_page(root: Path, head: str, atlas: Path, page: Path) -> dict[str, object]:
    parsed = parse_page(page)
    commit = parsed["commit"]
    commit_url = parsed["commit_url"]
    evidence_paths = parsed["evidence_paths"]
    relative_page = page.relative_to(atlas).as_posix()
    result: dict[str, object] = {
        "page": relative_page,
        "status": "unverified",
        "verified_commit": commit,
        "commits_behind": None,
        "evidence_paths": evidence_paths,
        "changed_evidence_paths": [],
        "reason": "verification commit is missing",
    }

    if not isinstance(commit, str):
        return result
    if not commit_exists(root, commit):
        if isinstance(commit_url, str) and commit_url.startswith(("http://", "https://")):
            result.update(
                status="external",
                reason="verification commit belongs to an external repository",
            )
        else:
            result.update(status="unknown_commit", reason="verification commit is not in this repository")
        return result

    code, full_commit = run_git(root, "rev-parse", commit)
    if code != 0:
        result.update(status="unknown_commit", reason="verification commit cannot be resolved")
        return result
    if full_commit == head:
        result.update(status="current", commits_behind=0, reason="page is verified at current HEAD")
        return result

    ancestor_code, _ = run_git(root, "merge-base", "--is-ancestor", full_commit, head)
    if ancestor_code != 0:
        result.update(status="diverged", reason="verification commit is not an ancestor of HEAD")
        return result

    _, behind_raw = run_git(root, "rev-list", "--count", f"{full_commit}..{head}")
    commits_behind = int(behind_raw) if behind_raw.isdigit() else None
    result["commits_behind"] = commits_behind

    if not evidence_paths:
        result.update(
            status="unmapped",
            reason="HEAD advanced but the page declares no machine-readable evidence paths",
        )
        return result

    diff_args = ["diff", "--name-only", f"{full_commit}..{head}", "--", *evidence_paths]
    diff_code, changed_raw = run_git(root, *diff_args)
    if diff_code != 0:
        result.update(status="review", reason="evidence path diff could not be computed")
        return result
    changed = sorted(line for line in changed_raw.splitlines() if line)
    result["changed_evidence_paths"] = changed
    if changed:
        result.update(status="review", reason="one or more declared evidence paths changed")
    else:
        result.update(
            status="unchanged_evidence",
            reason="HEAD advanced but declared evidence paths did not change",
        )
    return result


def build_report(repository: Path, atlas_path: str) -> dict[str, object]:
    root = git_root(repository)
    if root is None:
        raise ValueError(f"not a Git repository: {repository}")
    atlas = Path(atlas_path).expanduser()
    if not atlas.is_absolute():
        atlas = root / atlas
    atlas = atlas.resolve()
    if not atlas.is_dir():
        raise ValueError(f"Atlas directory does not exist: {atlas}")

    code, head = run_git(root, "rev-parse", "HEAD")
    if code != 0 or not head:
        raise ValueError(f"cannot resolve Git HEAD: {root}")

    pages = [
        analyze_page(root, head, atlas, page)
        for page in sorted(atlas.rglob("*.md"))
        if page.is_file()
    ]
    summary = dict(sorted(Counter(str(page["status"]) for page in pages).items()))
    return {
        "repository": str(root),
        "atlas": str(atlas),
        "head": head,
        "page_count": len(pages),
        "summary": summary,
        "needs_review": any(page["status"] in REVIEW_STATUSES for page in pages),
        "pages": pages,
    }


def detected_language(requested: str) -> str:
    if requested != "auto":
        return requested
    locale = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    return "zh" if locale.lower().startswith("zh") else "en"


def print_text(report: dict[str, object], language: str) -> None:
    zh = language == "zh"
    print("Project Atlas 新鲜度报告" if zh else "Project Atlas freshness report")
    print(f"{'仓库' if zh else 'Repository'}: {report['repository']}")
    print(f"Atlas: {report['atlas']}")
    print(f"HEAD: {str(report['head'])[:12]}")
    print(f"{'页面' if zh else 'Pages'}: {report['page_count']}")
    print()
    labels = STATUS_LABELS[language]
    for page in report["pages"]:
        status = str(page["status"])
        behind = page["commits_behind"]
        suffix = f", {'落后' if zh else 'behind'} {behind} {'个提交' if zh else 'commits'}" if behind else ""
        print(f"[{labels[status]}] {page['page']}{suffix}")
        changed = page["changed_evidence_paths"]
        if changed:
            prefix = "  变化证据" if zh else "  changed evidence"
            print(f"{prefix}: {', '.join(changed)}")
    print()
    if report["needs_review"]:
        print("结论：存在需要人工复核的页面。" if zh else "Result: one or more pages require review.")
    else:
        print("结论：未发现必须复核的本地证据变化。" if zh else "Result: no mandatory local evidence review found.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Project Atlas freshness against Git HEAD.")
    parser.add_argument("repository", nargs="?", default=".", help="Git repository to inspect")
    parser.add_argument("--atlas", default="docs/project-atlas", help="Atlas directory, relative to repository root")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format")
    parser.add_argument("--language", choices=("auto", "en", "zh"), default="auto", help="Text output language")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when a page requires review")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(Path(args.repository).expanduser(), args.atlas)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report, detected_language(args.language))
    if args.strict and report["needs_review"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
