# Architecture

> Status: Draft
> Last verified commit: `<git-sha>`
> Evidence: Stable modules and entrypoint wiring
> Evidence paths: `path/to/bootstrap`, `path/to/router`
> Known gaps: List explicitly

## Mental model

Give a one-screen explanation of the architecture and dependency direction.

## Components

| Component | Responsibility | Owns state | Depends on | Must not own |
|---|---|---|---|---|
| Add component | Add responsibility | Add state | Add dependencies | Add boundary |

## Request and event boundaries

Describe synchronous APIs, background jobs, queues, callbacks, and external integrations.

## Dependency rules

- Add intended dependency direction.
- Add cross-layer restrictions.
- Add transaction, cache, and external-call boundaries.

## Architectural pressure points

List areas where business rules are concentrated, responsibilities leak, or changes frequently cross boundaries.
