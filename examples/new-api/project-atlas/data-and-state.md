# Data and State Map

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E4, E8, E13-E15](evidence.md)
> Known gaps: Production TTL choices, Redis topology and log retention are deployment-specific

## Durable state

| State | Main writers | Main readers | Consistency boundary |
|---|---|---|---|
| `users`, `tokens` | User/token controllers and billing | Auth middleware and billing | GORM atomic updates; optional deferred batch deltas |
| `channels`, `abilities` | Channel admin and health automation | Distributor/channel cache | Some batch mutations use transactions; runtime cache refresh follows writes |
| `options` | Root settings APIs | Typed setting packages | DB write followed by local update; every node periodically reloads |
| `tasks` | Task submitter and poller | Task APIs and poller | CAS guards terminal transitions that trigger billing |
| subscription tables | Purchase/admin/reset and billing | Funding selection and settlement | Row locking and pre-consume records |
| `logs` | Relay, billing, audit and task flows | User/admin dashboards | May use separate DB or ClickHouse |
| `system_tasks` and locks | Scheduler/runner | Background workers | Unique active key plus renewable DB lease |

## Cache map

| Cache | Key/shape | TTL or refresh | Miss/failure behavior |
|---|---|---|---|
| Token cache | `token:<HMAC(raw-key)>` Redis hash | `SYNC_FREQUENCY`, default 60s | Falls back to SQL and asynchronously repopulates |
| User cache | `user:<id>` Redis hash | `SYNC_FREQUENCY`, default 60s | Falls back to SQL and asynchronously repopulates |
| Channel routing | `group → model → channel IDs` plus `channel ID → Channel` in memory | Full sync every `SYNC_FREQUENCY`; active refresh after admin mutations | Falls back to SQL only when memory cache is disabled, not when map content is stale |
| Options/settings | Global in-memory map and typed settings | Reload every `SYNC_FREQUENCY`; local write updates immediately | Existing process values remain until reload succeeds |
| Channel affinity | `new-api:channel_affinity:v1:*` | Rule TTL, default 3600s | Redis when enabled; local LRU only when Redis is disabled; Redis errors return an error |
| File/body cache | Disk or memory body storage | Size/config dependent | Used to replay bodies across retries and avoid repeated downloads |
| Batch accounting | Process-local maps by entity ID | Flush interval, default 5s when explicitly enabled | No durable queue was found for unflushed deltas |

## Important state transitions

```text
Token request
  → Redis/DB token snapshot
  → Redis/DB user snapshot
  → selected Channel from memory/DB
  → BillingSession pre-consume
  → upstream response usage
  → settle wallet/subscription and token quota
  → consumption log
```

```text
Async task
  → full pre-consume
  → task row with provider ID and billing snapshot
  → scheduled DB-leased poller
  → CAS terminal transition
  → one winner settles or refunds
```

## Verified consistency controls

- Token and user cache keys do not store the raw token in the Redis key; token keys are HMAC-derived.
- User/token quota deltas use atomic SQL expressions when written directly.
- Multi-key channel polling uses per-channel locks in process memory.
- Terminal task billing uses a status-guarded update to prevent multiple pollers settling the same transition.
- System tasks use a renewable per-type lease and unique active key.

## Inferred durability concern

When `BATCH_UPDATE_ENABLED=true`, user, token and channel quota deltas can live only in process memory until the next batch flush. The graceful shutdown path does not visibly flush these maps. A process crash or shutdown inside that window may lose SQL accounting deltas. This is an evidence-backed inference, not a reproduced incident.
