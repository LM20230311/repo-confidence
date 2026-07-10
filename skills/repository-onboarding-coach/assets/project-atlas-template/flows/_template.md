# Flow: <name>

> Status: Draft
> Last verified commit: `<git-sha>`
> Evidence: Add entrypoints, symbols, tests, migrations, or runtime observations
> Known gaps: List explicitly

## Mental model

Explain the flow in one screen.

## Trigger and entrypoint

- Trigger:
- Entrypoint:
- Caller:

## Preconditions

- Authentication:
- Authorization:
- Required state:
- Feature flags or configuration:

## Normal path

1. Add ordered step and evidence.

## State changes

| State | Read/write | Transaction or consistency boundary | Evidence |
|---|---|---|---|
| Add state | Read/Write | Add boundary | Add symbol |

## Failure paths

| Failure | Behavior | Retry/fallback/compensation | User-visible result |
|---|---|---|---|
| Add failure | Add behavior | Add recovery | Add result |

## Security and money

Describe permission, privacy, secret, billing, quota, and audit implications.

## Observability

List logs, metrics, traces, request IDs, dashboards, alerts, and state inspection points.

## Invariants

- Add testable invariant.

## Tests

- Existing coverage:
- Missing high-value coverage:

## Change hotspots

List common requirements and likely affected responsibilities.

## Known unknowns

- Add explicit question and verification path.
