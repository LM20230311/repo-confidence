# Change Brief

Use this template before implementing a non-trivial requirement. Keep it proportional: a small change may need one screen; a high-risk change may need a detailed brief.

## Request

- **Goal:** What user or system outcome is required?
- **Acceptance criteria:** What observable behavior proves completion?
- **Out of scope:** What must remain unchanged?
- **Assumptions:** Which interpretations are being made?

## Current behavior

- Entry point and main call path;
- source of truth;
- current state transitions;
- cache, queue, external service, and background-worker involvement;
- current tests and operational evidence.

Mark claims as `Verified`, `Inferred`, or `Unknown`.

## Proposed impact

| Area | Expected impact | Evidence |
|---|---|---|
| API or event contract | None / additive / breaking | Symbols or specs |
| Domain logic | Description | Symbols |
| Database and migration | Description | Models and migrations |
| Cache | Keys, TTL, invalidation | Cache code |
| Queue or async jobs | Events, retries, idempotency | Producers/consumers |
| External services | Protocol, credentials, rate limits | Clients/adapters |
| Authentication and authorization | Description | Middleware/policy |
| Billing and quota | Description | Pricing/settlement |
| Privacy and security | Description | Data flow |
| Observability | Logs, metrics, traces | Instrumentation |

## Failure analysis

- What can fail before state mutation?
- What can fail after partial state mutation?
- Which errors retry, fallback, compensate, or fail closed?
- Is the operation idempotent?
- Can concurrent requests violate an invariant?
- What happens when cache, database, queue, or upstream is unavailable?

## Invariants

List existing invariants that the change must preserve. Add new invariants introduced by the requirement.

## Implementation outline

List the smallest coherent set of changes by responsibility. Avoid committing to exact helper names before inspecting local conventions.

## Verification

### Focused checks

- tests for the changed behavior;
- failure and boundary cases;
- authorization, billing, idempotency, and cache invalidation when relevant.

### Broader checks

- package or module test suite;
- integration or contract tests;
- migration compatibility;
- static checks, lint, or build.

### Runtime observation

- logs, metrics, traces, database rows, cache entries, queue events;
- expected success signal;
- expected failure signal.

## Rollout and rollback

- feature flag or compatibility strategy;
- data backfill or dual-read/write needs;
- rollback command or code path;
- irreversible state changes;
- post-deploy monitoring window.

## Unknowns and decision points

For each unresolved item, record:

- why it matters;
- whether it blocks implementation;
- the safest way to verify;
- who or what can answer it.

## Risk rating

- `Low`: local, reversible, no shared state or contract impact.
- `Medium`: shared state or behavior change with strong test and rollback coverage.
- `High`: authentication, billing, destructive migration, public contract, distributed consistency, or difficult rollback.

Do not lower risk because AI generated the implementation quickly.
