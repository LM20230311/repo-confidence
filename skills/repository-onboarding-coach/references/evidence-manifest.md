# Evidence Manifest

## Purpose

The Evidence Manifest is a deterministic, machine-readable bridge between a
repository inventory and human-reviewed Flow Cards. It identifies where useful
evidence is likely to exist before an AI claims to understand a business flow.

It does not prove runtime behavior. Static registrations, nearby tests, and
migrations are candidates that must be verified with CodeGraph, source reading,
tests, or runtime evidence.

## Command

```bash
python3 scripts/evidence_manifest.py <repository> --summary --max-items 20
```

The script is read-only. It emits JSON to standard output and does not write to
the target repository.

## Schema

Top-level fields:

- `schema_version`: manifest schema version;
- `repository`: root, Git HEAD, branch, and tracked dirty-file count;
- `inventory_counts`: totals inherited from the structural inventory;
- `semantic_counts`: static registrations and flow-candidate totals;
- `evidence`: source candidates and their extracted structure;
- `flow_candidates`: ranked starting points for human/AI investigation;
- `notes`: explicit limitations.

Each evidence item records:

- repository-relative path and language;
- structural roles such as entrypoint, route, worker, or persistence;
- parse status;
- Python definitions and supported framework registrations;
- heuristic test and migration relations;
- a status that requires further verification.

## Current semantic coverage

Version 1 uses Python's standard-library AST to identify:

- Django `path` and `re_path` registrations;
- DRF-style router `register` calls;
- decorated task functions such as Huey, Celery, and Django task decorators;
- persistence classes inheriting from `Model` or `Document`.

Other languages still receive path-based evidence entries. Their semantic parse
status is `semantic_parser_not_available`, so the caller can use CodeGraph or a
language-specific follow-up rather than assuming an empty result means no flow
exists.

## Confidence boundaries

- `candidate_requires_verification` means the file is structurally relevant.
- `heuristic_candidate` means a test or migration is related by package and token
  similarity, not a proven dependency.
- `candidate_not_verified_call_graph` means the registration is a useful flow
  starting point, not an end-to-end business flow.
- `discovery_score` ranks explicit registrations above generic state candidates;
  it does not measure business criticality.

Never convert these statuses to `Verified` without checking implementation,
callers or consumers, failure paths, and executable tests.

## Privacy and safety

The manifest includes paths, symbol names, route literals, decorators, and class
bases. It does not include function bodies or configuration values. Source files
larger than the safety limit are skipped and reported rather than copied.

Run it only on repositories the user is authorized to inspect, and do not publish
private manifest output without organizational approval.
