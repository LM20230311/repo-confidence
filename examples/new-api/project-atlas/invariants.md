# System Invariants

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [Evidence index](evidence.md), executed selected backend tests
> Known gaps: Several invariants lack end-to-end or failure-injection coverage

| Invariant | Severity | Enforced by | Verification |
|---|---|---|---|
| Invalid/expired/exhausted token must not reach a provider | Critical | `TokenAuth`, `ValidateUserToken` | Source; no full middleware integration run |
| Disabled user must be rejected even with a cached token | Critical | `GetUserCache` status check | Source |
| Token model/group restrictions apply before channel execution | High | Token context plus `Distribute` | Source |
| Higher-priority channels are selected before lower-priority retry tiers | High | channel cache sorting and retry index | Source; direct deterministic test missing |
| A billing multiplier must not create a negative charge through overflow/NaN | Critical | bounds, Decimal, saturating quota helpers | Quota and billing-expression tests passed |
| Pre-consume and settle use one frozen expression/request snapshot | Critical | `BillingSnapshot`, `BillingRequestInput` | Tiered-settlement tests passed |
| Failed request refunds pre-consumed funding at most once per live session | Critical | BillingSession mutex/state | Source; process-crash behavior unknown |
| Terminal async billing occurs only for the CAS winner | Critical | `Task.UpdateWithStatus` | CAS and task billing tests passed |
| Channel secrets are hidden from normal admin responses and logs | Critical | masked responses, audit field filtering | Token/channel tests and source |
| Channel status changes use dedicated operational permissions | High | route permission table and controller validation | Router/controller tests passed |
| DB code remains compatible with SQLite, MySQL and PostgreSQL | High | repository policy and dialect branches | Selected SQLite tests; external DB suites not run |
| Provider request conversion preserves explicit zero values | High | pointer DTO policy and regression tests | Selected relay/helper tests passed |

## Unverified invariants

- Every stream path stops retrying after client-visible output begins.
- Every payment webhook is cryptographically verified before crediting quota.
- Every batch-accounting delta is durably flushed during graceful shutdown.
- Every channel mutation keeps `channels` and `abilities` atomic on failure.
- Every async bulk-failure path applies the intended refund policy exactly once.
