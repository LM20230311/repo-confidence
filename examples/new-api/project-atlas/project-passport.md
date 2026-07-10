# Project Passport

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E1, E2, E14, E16, E17](evidence.md)
> Known gaps: Frontend build and full production deployment were not executed

## Purpose

- Product goal: aggregate many AI providers behind compatible APIs and operate users, channels, pricing, quota, payments, usage and administrative workflows.
- Primary users: API consumers, end users managing tokens and quota, and operators managing upstream channels and pricing.
- Main boundary: it is both a protocol gateway and a stateful commercial/organizational control plane.
- Upstream origin: built from One API and maintained under the New API identity.

## Technology

| Area | Verified implementation |
|---|---|
| Backend | Go module requiring Go `1.25.1`, Gin, GORM v2 |
| Default frontend | React 19, TypeScript, Rsbuild, Tailwind, TanStack Query/Router |
| Classic frontend | Separate React frontend retained for compatibility |
| Primary database | SQLite by default; MySQL and PostgreSQL supported |
| Log database | Primary DB by default; optional separate SQLite/MySQL/PostgreSQL or ClickHouse |
| Cache | Optional Redis plus process-local caches |
| Authorization | Session roles, API tokens, Casbin-backed granular admin permissions |
| Deployment | Multi-stage Docker image; Compose example includes PostgreSQL and Redis |
| License | GNU AGPL v3 |

The inventory counted 2,183 tracked/unignored files: 646 Go, 979 TypeScript, and 410 JavaScript files. File counts describe repository shape, not runtime importance.

## Entry points

| Entry | Type | Responsibility |
|---|---|---|
| `main.main` | Process | Initializes state, caches, tasks, Gin server and graceful shutdown |
| `router.SetApiRouter` | HTTP `/api` | Users, tokens, channels, pricing, payments, logs, subscriptions and admin APIs |
| `router.SetRelayRouter` | HTTP `/v1`, `/v1beta`, `/mj`, `/suno` | OpenAI, Claude, Gemini and task-compatible relay APIs |
| `router.SetDashboardRouter` | Compatibility HTTP | Legacy dashboard usage endpoints |
| `router.SetVideoRouter` | HTTP | Video submission, retrieval and content proxy |
| `service.StartSystemTaskRunner` | Background worker | Scheduled channel tests, model updates, async polling and cleanup tasks |

## State and dependencies

| System | Role | Source of truth | Failure consequence |
|---|---|---|---|
| Primary SQL DB | Users, tokens, channels, abilities, quota, tasks, options, subscriptions | SQL tables | Most authenticated and relay operations fail or become stale |
| Log DB | Consumption, error and audit records | `LOG_DB` | Requests may continue but observability/accounting history degrades |
| Redis | Token/user caches, quota deltas, affinity and distributed fast state | SQL remains authoritative for user/config entities | Cache reads usually fall back to DB; some hybrid-cache operations return errors |
| In-memory maps | Channel routing, option settings, batch counters | Periodically rebuilt from DB or flushed to DB | Per-process staleness or loss on crash is possible |
| Upstream AI providers | Model execution and media tasks | Provider APIs | Retry, fallback, auto-disable or user-visible failure |
| Payment providers | Top-up and subscription collection | Provider callbacks plus local orders | Financial reconciliation risk |

## Commands

```text
Run dev stack:          make dev
Build embedded UIs:     make build-all-web
Run after UI build:     go run main.go
Selected backend tests: go test ./common ./model ./service ./controller ./router \
                          ./middleware ./relay ./relay/common ./relay/helper \
                          ./pkg/billingexpr -count=1
Frontend checks:        cd web/default && bun run typecheck && bun run lint
Docker:                 docker compose up -d
```

The clean source checkout does not contain the embedded `web/*/dist` directories. Building or testing the root `main` package therefore requires building the frontend assets first. This case executed only the selected backend packages listed in [test-map.md](test-map.md).

## Repository policies

- Preserve support for SQLite, MySQL and PostgreSQL.
- Use the project's JSON wrappers rather than direct `encoding/json` operations in business code.
- Preserve explicit zero values in upstream request DTOs.
- Treat billing arithmetic, saturation, pre-consume and settlement as protected invariants.
- Read the expression billing contract before modifying tiered pricing.
- Preserve upstream project branding and attribution.
- Use Bun for the default frontend.

## Deployment shape

One Go binary embeds both compiled frontend themes and exposes port 3000 by default. Master nodes run migrations and scheduled tasks; slave nodes skip primary migrations and system-task runner startup. Multi-node state propagation depends on SQL, Redis where enabled, periodic option/channel synchronization, and DB-backed task leases.
