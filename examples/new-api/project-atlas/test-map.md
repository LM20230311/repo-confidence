# Test Map

> Status: Verified for executed scope
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: Test source plus local command result on 2026-07-10
> Known gaps: Frontend, live providers, payments and external database integration were not executed

## Executed command

```bash
go test ./common ./model ./service ./controller ./router ./middleware \
  ./relay ./relay/common ./relay/helper ./pkg/billingexpr -count=1
```

All ten packages passed.

## Behavior-to-test map

| Behavior | Representative tests | Coverage confidence |
|---|---|---|
| Saturating quota conversion | `common/quota_math_test.go` | High for helper boundaries |
| Tiered expression evaluation and snapshot settlement | `pkg/billingexpr/*_test.go`, `service/tiered_settle_test.go` | High for calculation logic |
| Cache/image/audio token normalization | `service/text_quota_test.go` | High for documented cases |
| Task refund and delta settlement | `service/task_billing_test.go` | High for SQLite-backed unit scenarios |
| Task terminal concurrency | `model/task_cas_test.go` | High for process-level DB race simulation |
| System-task leasing and deduplication | `model/system_task_test.go`, `service/system_task_test.go` | High for tested DB lifecycle |
| Channel mutation permissions | `controller/channel_authz_test.go`, `router/channel_router_test.go` | High for route/field classification |
| Token key privacy and ownership | `controller/token_test.go` | High for controller responses |
| Provider request/response conversion | tests under `relay/channel/*` | Uneven by provider; not all packages executed here |
| Channel affinity | `service/channel_affinity_*_test.go` | Medium/High for rule/cache helpers |

## Highest-value missing tests

1. TokenAuth integration across Redis hit, Redis failure, disabled user, IP limits and group override.
2. Deterministic channel priority/weight/retry tests with cache and DB parity.
3. Stream failure after first client-visible chunk across representative adaptors.
4. Crash recovery between wallet/subscription settlement and token adjustment.
5. Batch-accounting shutdown/crash durability.
6. Channel update rollback when Ability rebuild fails.
7. MySQL and PostgreSQL CI for migrations, locks and quota updates.
8. Payment webhook signature, replay and idempotency matrix.
