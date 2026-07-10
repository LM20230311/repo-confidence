# Maintenance Competency Rubric

Assess observable maintenance behavior by domain. A developer may be L3 in API work and L1 in billing; avoid assigning a single global level without context.

## L1 — Navigator

The developer can:

- state the system purpose and primary users;
- run the project and focused tests;
- identify main entrypoints and module boundaries;
- use CodeGraph, search, and Git to locate relevant code;
- distinguish current code evidence from documentation or assumption;
- name major data stores and external dependencies.

Evidence examples:

- traces a request from route to service and persistence;
- explains where repository instructions apply;
- finds the nearest relevant test without being given a filename.

Not yet sufficient for:

- unsupervised changes to high-risk state or core invariants.

## L2 — Contributor

The developer can:

- complete a scoped, reversible change;
- predict the main affected modules before AI edits;
- identify schema, cache, contract, and test impact;
- explain the resulting diff in business terms;
- add meaningful regression coverage;
- recognize when a requirement touches a high-risk domain;
- update the relevant Project Atlas knowledge.

Evidence examples:

- adds validation or an additive field with correct tests;
- fixes a cache invalidation path and demonstrates stale-state behavior;
- explains why unrelated files did not need modification.

Not yet sufficient for:

- owning billing, auth, destructive migrations, distributed workflows, or public compatibility without review.

## L3 — Maintainer

The developer can:

- modify a critical business flow while preserving invariants;
- reason about normal, failure, retry, fallback, compensation, and partial success;
- design and review migrations and compatibility strategies;
- handle cache consistency, idempotency, concurrency, and async jobs;
- produce a realistic rollout, observation, and rollback plan;
- diagnose production symptoms using logs, metrics, traces, and state;
- review AI-generated changes for missing cross-layer impact.

Evidence examples:

- changes pricing or quota behavior with snapshot and reconciliation tests;
- adds a provider integration with retry and credential-rotation behavior;
- resolves an incident and updates the risk map and playbook.

## L4 — Owner

The developer can:

- define architecture and operational direction;
- prioritize technical debt by business risk;
- coordinate cross-system changes and incident response;
- decide which invariants, compatibility promises, and service levels matter;
- approve or reject high-risk AI-generated changes;
- coach others and maintain the project's knowledge system;
- identify when the current model or architecture is no longer adequate.

Evidence examples:

- leads a safe migration across services;
- establishes a new reliability or billing control plane;
- turns repeated incidents into architectural improvements and team practices.

## Assessment method

Use four evidence types:

1. **Explain:** Teach back a core flow without source access.
2. **Predict:** Analyze a realistic requirement before implementation.
3. **Change:** Complete and explain a real scoped change.
4. **Recover:** Diagnose or simulate a failure and propose safe recovery.

Reading documentation proves orientation, not maintenance readiness. Quiz performance proves recall, not production ownership. Prefer evidence from real changes and failure handling.

## Recommended assessment prompts

### Navigation

- Where does this request or event enter?
- Which module owns the business decision?
- Which state is authoritative?

### Causality

- Why is this cache present?
- Why does this flow retry or fail closed?
- What happens if the process dies between these two writes?

### Change impact

- Which modules would a new requirement affect?
- Which files would you expect not to change, and why?
- Which invariant is easiest to break accidentally?

### Verification

- What focused test would fail before the fix?
- Which runtime signal proves the feature works?
- How would you detect and roll back a bad deployment?

## Reporting format

Report readiness by domain:

```text
Domain: Billing
Current level: L1
Verified evidence: Traced estimate and settlement paths
Missing evidence: No real pricing change or reconciliation test
Unsafe scope: Production multiplier or refund changes
Next task: Add a read-only pricing preview with table-driven tests
```

Never present the level as a personality judgment. It describes currently observed evidence and can change after the next real task.
