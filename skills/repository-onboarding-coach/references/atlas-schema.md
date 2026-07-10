# Project Atlas Schema

## Contents

1. Purpose
2. Required metadata
3. Recommended structure
4. Page types
5. Critical-flow selection
6. Evidence requirements
7. Freshness rules
8. Quality checks

## 1. Purpose

A Project Atlas is a navigable maintenance model, not an exhaustive code encyclopedia. It should let a developer recover the system model quickly, trace critical behavior, identify risk, and prepare safe changes.

Optimize for these questions:

- What is this system responsible for?
- Where does a request, event, or job enter?
- Which modules own each responsibility?
- Which state is authoritative?
- What is cached or asynchronous?
- What can fail or partially succeed?
- Which invariants cannot be broken?
- How can a change be verified and rolled back?

## 2. Required metadata

Every Atlas page must begin with metadata equivalent to:

```markdown
> Status: Verified | Partially verified | Draft
> Last verified commit: `<git-sha>`
> Evidence: `path:symbol`, `test`, `migration`
> Evidence paths: `repository/relative/file`, `tests/relative/test_file`
> Known gaps: short explicit list or `None known`
```

Use stable symbol names when possible. Line numbers may be added for convenience but should not be the only locator.

`Evidence` is the human-readable explanation. `Evidence paths` is the
machine-readable, repository-relative file list used by the freshness checker.
List only files that materially support the page. An omitted path is reported as
unmapped rather than guessed.

## 3. Recommended structure

```text
docs/project-atlas/
├── index.md
├── project-passport.md
├── architecture.md
├── glossary.md
├── entities/
├── flows/
├── data-and-state.md
├── cache-map.md
├── external-dependencies.md
├── invariants.md
├── risk-map.md
├── change-briefs/
├── test-map.md
└── known-unknowns.md
```

Create only useful pages. Small projects may combine data, cache, dependencies, risks, and tests into fewer files.

## 4. Page types

### Index

Keep the index short. Include:

- one-paragraph system purpose;
- project maturity and deployment shape;
- links to the most important flows;
- high-risk domains;
- current known unknowns;
- latest verification commit.

### Project passport

Record:

- repository name and purpose;
- primary users and use cases;
- languages and frameworks;
- build, test, lint, and run commands;
- executable entrypoints and workers;
- data stores, caches, queues, and external systems;
- deployment model;
- applicable repository instructions;
- local development prerequisites.

### Architecture

Describe responsibility boundaries and dependency direction. Prefer domain and layer relationships over directory listing.

For each major component, record:

- responsibility;
- public interfaces;
- state owned;
- dependencies;
- forbidden or risky dependency directions.

### Glossary

For each term, record:

- concise business meaning;
- corresponding code entity;
- source of truth;
- related flows;
- common confusion.

### Entity page

Record:

- purpose and identity;
- database or persistence representation;
- lifecycle and valid state transitions;
- creators, readers, writers, and deleters;
- cache representation;
- invariants and authorization boundaries;
- important tests and migrations.

### Flow Card

Use this structure:

```markdown
# <Flow name>

## Mental model
One-screen explanation.

## Trigger and entrypoint
API, event, schedule, CLI, callback, or internal call.

## Preconditions
Authentication, authorization, feature flags, required state.

## Normal path
Ordered steps with symbols and state transitions.

## State changes
Tables, cache keys, queues, external resources, transactions.

## Failure paths
Errors, retries, fallback, compensation, idempotency, partial success.

## Security and money
Permissions, secrets, privacy, quota, billing, audit.

## Observability
Logs, metrics, traces, request IDs, dashboards, alerts.

## Invariants
Behavior that must remain true.

## Tests
Current coverage and important missing cases.

## Change hotspots
Common requirements and affected modules.

## Known unknowns
Questions that still require proof.
```

### Data and state map

For each state system, record:

- source of truth;
- writers and readers;
- transaction or consistency boundary;
- retention and lifecycle;
- recovery behavior;
- failure mode.

### Cache map

For each cache, record:

- key format;
- cached value;
- TTL;
- warmup and cache-miss behavior;
- invalidation triggers;
- stale-data consequence;
- multi-instance consistency behavior;
- fail-open or fail-closed semantics.

### Invariants

Prefer testable statements:

- An expired credential must never reach an upstream provider.
- A failed payment callback must not credit balance.
- A retry must not create a duplicate order.
- A billing configuration change must not alter an in-flight async task's price snapshot.

For each invariant, record enforcement points, tests, severity, and recovery strategy.

### Risk map

Classify risk by domain and failure impact:

- authentication and authorization;
- money, billing, quota, and accounting;
- destructive data changes and migrations;
- concurrency, idempotency, and distributed locks;
- cache consistency;
- compatibility and public API contracts;
- privacy and secrets;
- async jobs, retries, and callbacks;
- external provider behavior;
- rollout and operational recovery.

### Test map

Map critical behavior to tests. Identify whether coverage verifies:

- happy path;
- failure and retry;
- permission boundary;
- billing or state invariant;
- migration compatibility;
- concurrency or idempotency;
- external protocol translation.

## 5. Critical-flow selection

Score flow candidates from 0 to 3 for:

- business criticality;
- write or monetary impact;
- security sensitivity;
- cross-module span;
- asynchronous or distributed complexity;
- incident frequency;
- requirement frequency.

Document the highest-scoring flows first. Include at least one administrative mutation flow and one failure/recovery flow when relevant.

## 6. Evidence requirements

### Verified claim

Require at least one direct implementation source. For high-risk claims, also require a test, migration, or runtime observation.

### Inferred claim

State what evidence exists and what is missing. Do not convert inference to fact because multiple files agree by naming.

### Unknown claim

Record the question, why it matters, and the cheapest safe way to verify it.

### Evidence precedence

Use this practical order:

1. current executable behavior or focused test;
2. current implementation and schema;
3. current configuration and deployment code;
4. Git history and design documents;
5. comments and naming;
6. intuition.

Lower-precedence evidence may explain intent but should not override current behavior.

## 7. Freshness rules

- Record the verified commit on every critical page.
- Record explicit repository-relative evidence paths for automatic comparison.
- Compare changed symbols, not only changed filenames.
- Re-verify affected flows after behavior changes.
- Do not update the verified commit on untouched pages without checking them.
- Mark stale pages explicitly when verification is incomplete.
- Keep generated indexes separate from human-confirmed invariants.

Use `scripts/atlas_freshness.py <repo> --atlas docs/project-atlas` for the
deterministic first pass. Its statuses mean:

| Status | Meaning |
|---|---|
| `current` | Page verification commit equals current HEAD |
| `unchanged_evidence` | HEAD advanced but declared evidence files did not change |
| `review` | One or more declared evidence files changed |
| `unmapped` | HEAD advanced but the page declares no evidence paths |
| `diverged` | Verification commit is not an ancestor of HEAD |
| `unverified` / `unknown_commit` | Verification metadata cannot be trusted |
| `external` | The page intentionally points at another repository's commit |

The checker identifies candidates; it does not prove semantic freshness. Use
CodeGraph, source, tests and history before updating the verified commit.

## 8. Quality checks

An Atlas is useful when a newcomer can:

- explain the system in five minutes;
- locate a core flow in ten minutes;
- identify source of truth and cache behavior;
- predict the likely impact of a representative change;
- name the most dangerous invariant in each critical domain;
- design a proportional verification and rollback plan.

Reject or revise an Atlas that is mostly directory summaries, contains uncited certainty, hides unknowns, or cannot support a real change discussion.
