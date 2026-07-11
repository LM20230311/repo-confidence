#!/usr/bin/env python3
"""Build a deterministic evidence manifest for repository onboarding.

The manifest connects structural candidates with framework registrations, nearby
tests, and migrations. It never claims to prove a runtime call graph.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from repo_inventory import LANGUAGE_BY_SUFFIX, build_inventory  # noqa: E402


MAX_SOURCE_BYTES = 2 * 1024 * 1024
DEFAULT_RELATED_LIMIT = 8
GENERIC_TOKENS = {
    "api",
    "app",
    "apps",
    "index",
    "main",
    "model",
    "models",
    "route",
    "routes",
    "routing",
    "test",
    "tests",
    "task",
    "tasks",
    "url",
    "urls",
    "worker",
    "workers",
}


def dotted_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def value_label(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float)):
        return str(node.value)
    name = dotted_name(node)
    if name:
        return name
    if isinstance(node, ast.Call):
        callee = dotted_name(node.func)
        if callee:
            arguments = [value_label(argument) for argument in node.args[:2]]
            rendered = ", ".join(argument for argument in arguments if argument)
            return f"{callee}({rendered})"
    return None


def keyword_label(call: ast.Call, keyword: str) -> str | None:
    for item in call.keywords:
        if item.arg == keyword:
            return value_label(item.value)
    return None


def decorator_name(decorator: ast.AST) -> str | None:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return dotted_name(target)


def is_task_decorator(name: str) -> bool:
    leaf = name.rsplit(".", 1)[-1].lower()
    return leaf in {
        "background",
        "db_task",
        "job",
        "periodic_task",
        "shared_task",
        "task",
    }


def parse_python_source(source_path: Path) -> dict[str, object]:
    """Extract structural Python evidence without returning source contents."""
    try:
        if source_path.stat().st_size > MAX_SOURCE_BYTES:
            return {
                "parse_status": "skipped_too_large",
                "definitions": {"functions": [], "classes": []},
                "route_registrations": [],
                "task_registrations": [],
                "model_classes": [],
            }
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_path))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        return {
            "parse_status": "error",
            "parse_error": type(error).__name__,
            "definitions": {"functions": [], "classes": []},
            "route_registrations": [],
            "task_registrations": [],
            "model_classes": [],
        }

    top_level_functions: list[str] = []
    top_level_classes: list[str] = []
    task_registrations: list[dict[str, object]] = []
    model_classes: list[dict[str, object]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_functions.append(node.name)
            decorators = [
                name
                for decorator in node.decorator_list
                if (name := decorator_name(decorator))
            ]
            task_decorators = [name for name in decorators if is_task_decorator(name)]
            if task_decorators:
                task_registrations.append(
                    {
                        "symbol": node.name,
                        "line": node.lineno,
                        "decorators": task_decorators,
                    }
                )
        elif isinstance(node, ast.ClassDef):
            top_level_classes.append(node.name)
            bases = [name for base in node.bases if (name := dotted_name(base))]
            if any(base.rsplit(".", 1)[-1] in {"Document", "Model"} for base in bases):
                model_classes.append(
                    {"symbol": node.name, "line": node.lineno, "bases": bases}
                )

    route_registrations: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = dotted_name(node.func)
        if not callee:
            continue
        leaf = callee.rsplit(".", 1)[-1]
        if leaf in {"path", "re_path"}:
            route_registrations.append(
                {
                    "style": leaf,
                    "line": node.lineno,
                    "route": value_label(node.args[0]) if node.args else None,
                    "handler": value_label(node.args[1]) if len(node.args) > 1 else None,
                    "name": keyword_label(node, "name"),
                }
            )
        elif leaf == "register" and isinstance(node.func, ast.Attribute):
            route_registrations.append(
                {
                    "style": "router.register",
                    "line": node.lineno,
                    "router": dotted_name(node.func.value),
                    "route": value_label(node.args[0]) if node.args else None,
                    "handler": value_label(node.args[1]) if len(node.args) > 1 else None,
                    "name": keyword_label(node, "basename"),
                }
            )

    route_registrations.sort(key=lambda item: int(item["line"]))
    task_registrations.sort(key=lambda item: int(item["line"]))
    model_classes.sort(key=lambda item: int(item["line"]))
    return {
        "parse_status": "parsed",
        "definitions": {
            "functions": top_level_functions,
            "classes": top_level_classes,
        },
        "route_registrations": route_registrations,
        "task_registrations": task_registrations,
        "model_classes": model_classes,
    }


def tokenize(value: str) -> set[str]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", expanded)
        if len(token) > 2
    }
    return tokens - GENERIC_TOKENS


def package_root(path: str) -> str | None:
    parts = Path(path).parts
    return parts[0] if len(parts) > 1 else None


def related_paths(
    evidence_path: str,
    semantic_values: list[str],
    candidates: list[str],
    limit: int,
) -> dict[str, object]:
    evidence_tokens = tokenize(evidence_path)
    for value in semantic_values:
        evidence_tokens.update(tokenize(value))
    root = package_root(evidence_path)
    source_stem = Path(evidence_path).stem.lower().rstrip("s")

    ranked: list[tuple[int, str]] = []
    for candidate in candidates:
        overlap = len(evidence_tokens & tokenize(candidate))
        same_package = bool(root and package_root(candidate) == root)
        if not overlap and not same_package:
            continue
        candidate_stem = Path(candidate).stem.lower().rstrip("s")
        stem_match = bool(source_stem and source_stem in candidate_stem)
        ranked.append(
            (overlap * 10 + int(same_package) + (100 if stem_match else 0), candidate)
        )
    ranked.sort(key=lambda item: (-item[0], item[1]))
    paths = [path for _, path in ranked[:limit]]
    return {
        "status": "heuristic_candidate",
        "matched_count": len(ranked),
        "paths": paths,
        "truncated": len(ranked) > len(paths),
    }


def semantic_values(parsed: dict[str, object]) -> list[str]:
    values: list[str] = []
    definitions = parsed.get("definitions", {})
    if isinstance(definitions, dict):
        for key in ("functions", "classes"):
            items = definitions.get(key, [])
            if isinstance(items, list):
                values.extend(str(item) for item in items)
    for key in ("route_registrations", "task_registrations", "model_classes"):
        items = parsed.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            for field in ("route", "handler", "name", "symbol"):
                value = item.get(field)
                if value:
                    values.append(str(value))
    return values


def build_flow_candidates(evidence: list[dict[str, object]]) -> list[dict[str, object]]:
    flows: list[dict[str, object]] = []
    for item in evidence:
        evidence_id = str(item["id"])
        path = str(item["path"])
        relations = item.get("relations", {})
        has_tests = bool(
            isinstance(relations, dict)
            and isinstance(relations.get("tests"), dict)
            and relations["tests"].get("paths")
        )
        parsed = item.get("python", {})
        if not isinstance(parsed, dict):
            continue

        for route in parsed.get("route_registrations", []):
            if not isinstance(route, dict):
                continue
            score = 60 + (10 if has_tests else 0)
            raw_trigger = route.get("route")
            trigger = (
                "<root route>"
                if raw_trigger == ""
                else raw_trigger
                if raw_trigger is not None
                else "<dynamic route>"
            )
            handler = route.get("handler") or "<framework-resolved handler>"
            flows.append(
                {
                    "id": f"http:{path}:{route.get('line')}",
                    "kind": "http_entry",
                    "title": f"{trigger} -> {handler}",
                    "discovery_score": score,
                    "score_reasons": [
                        "explicit_route_registration",
                        *(["related_test_candidate"] if has_tests else []),
                    ],
                    "evidence_ids": [evidence_id],
                    "status": "candidate_not_verified_call_graph",
                }
            )

        for task in parsed.get("task_registrations", []):
            if not isinstance(task, dict):
                continue
            score = 65 + (10 if has_tests else 0)
            flows.append(
                {
                    "id": f"background:{path}:{task.get('line')}",
                    "kind": "background_task",
                    "title": str(task.get("symbol") or "<anonymous task>"),
                    "discovery_score": score,
                    "score_reasons": [
                        "explicit_task_decorator",
                        *(["related_test_candidate"] if has_tests else []),
                    ],
                    "evidence_ids": [evidence_id],
                    "status": "candidate_not_verified_call_graph",
                }
            )

        for model in parsed.get("model_classes", []):
            if not isinstance(model, dict):
                continue
            score = 40 + (10 if has_tests else 0)
            flows.append(
                {
                    "id": f"state:{path}:{model.get('line')}",
                    "kind": "state_lifecycle",
                    "title": str(model.get("symbol") or "<anonymous model>"),
                    "discovery_score": score,
                    "score_reasons": [
                        "explicit_persistence_model",
                        *(["related_test_candidate"] if has_tests else []),
                    ],
                    "evidence_ids": [evidence_id],
                    "status": "candidate_not_verified_call_graph",
                }
            )

    return sorted(
        flows,
        key=lambda item: (-int(item["discovery_score"]), str(item["id"])),
    )


def build_manifest(root: Path, related_limit: int = DEFAULT_RELATED_LIMIT) -> dict[str, object]:
    root = root.resolve()
    inventory = build_inventory(root)
    candidate_roles = {
        "entrypoint": inventory["entrypoint_candidates"],
        "route": inventory["route_candidates"],
        "worker": inventory["worker_candidates"],
        "persistence": inventory["persistence_candidates"],
    }
    roles_by_path: dict[str, list[str]] = {}
    for role, paths in candidate_roles.items():
        for path in paths:
            roles_by_path.setdefault(str(path), []).append(role)

    tests = [str(path) for path in inventory["test_files"]]
    migrations = [str(path) for path in inventory["migration_files"]]
    evidence: list[dict[str, object]] = []
    for path in sorted(roles_by_path):
        suffix = Path(path).suffix.lower()
        language = LANGUAGE_BY_SUFFIX.get(suffix, "Unknown")
        parsed: dict[str, object]
        if suffix == ".py":
            parsed = parse_python_source(root / path)
        else:
            parsed = {
                "parse_status": "semantic_parser_not_available",
                "definitions": {"functions": [], "classes": []},
                "route_registrations": [],
                "task_registrations": [],
                "model_classes": [],
            }
        values = semantic_values(parsed)
        evidence.append(
            {
                "id": f"source:{path}",
                "kind": "source_candidate",
                "path": path,
                "language": language,
                "roles": sorted(roles_by_path[path]),
                "status": "candidate_requires_verification",
                "python": parsed,
                "relations": {
                    "tests": related_paths(path, values, tests, related_limit),
                    "migrations": related_paths(
                        path, values, migrations, related_limit
                    ),
                },
            }
        )

    flows = build_flow_candidates(evidence)
    semantic_counts = {
        "route_registrations": sum(
            len(item["python"]["route_registrations"]) for item in evidence
        ),
        "task_registrations": sum(
            len(item["python"]["task_registrations"]) for item in evidence
        ),
        "model_classes": sum(
            len(item["python"]["model_classes"]) for item in evidence
        ),
        "flow_candidates": len(flows),
    }
    return {
        "schema_version": "1.0",
        "repository": {
            "root": inventory["repository"]["resolved_path"],
            "head": inventory["git"]["head"],
            "branch": inventory["git"]["branch"],
            "dirty_tracked_file_count": inventory["git"][
                "dirty_tracked_file_count"
            ],
        },
        "inventory_counts": inventory["path_counts"],
        "semantic_counts": semantic_counts,
        "evidence": evidence,
        "flow_candidates": flows,
        "notes": [
            "Source registrations are static evidence, not a verified runtime call graph.",
            "Test and migration relations are heuristic candidates and require review.",
            "Python AST enrichment currently covers route registrations, task decorators, and persistence model classes.",
            "No source bodies or configuration values are included in the manifest.",
        ],
    }


def summarize_manifest(manifest: dict[str, object], max_items: int) -> dict[str, object]:
    summary = json.loads(json.dumps(manifest, ensure_ascii=False))
    truncated: dict[str, dict[str, int]] = {}
    for field in ("evidence", "flow_candidates"):
        items = summary.get(field)
        if isinstance(items, list) and len(items) > max_items:
            truncated[field] = {"shown": max_items, "total": len(items)}
            summary[field] = items[:max_items]
    summary["truncated_lists"] = truncated
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only evidence manifest for repository onboarding."
    )
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--related-limit", type=int, default=DEFAULT_RELATED_LIMIT)
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repository).expanduser()
    if not root.is_dir():
        print(f"error: repository path is not a directory: {root}", file=sys.stderr)
        return 2
    if args.max_items < 1 or args.related_limit < 1:
        print("error: limits must be positive integers", file=sys.stderr)
        return 2
    manifest = build_manifest(root, related_limit=args.related_limit)
    if args.summary:
        manifest = summarize_manifest(manifest, args.max_items)
    if args.compact:
        print(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
