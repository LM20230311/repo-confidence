# Risk Map

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [Evidence index](evidence.md), flow cards, selected tests
> Known gaps: Incident history and deployment-specific controls were not reviewed

| Domain | Risk | Likelihood | Impact | Existing control | Missing evidence/control |
|---|---|---:|---:|---|---|
| Billing | Funding succeeds but token adjustment fails | Low/Medium | Critical | Session state prevents incorrect refund; logs failure | Durable reconciliation job not identified |
| Billing | Process dies during async wallet refund | Low/Medium | Critical | In-process idempotence | Wallet refund is non-idempotent and not a durable task |
| Batch accounting | Unflushed in-memory deltas are lost | Medium when enabled | High | Short flush interval | No shutdown flush or durable queue found |
| Routing | Channel and Ability rows diverge after partial update | Low/Medium | High | `FixAbility`, cache rebuild | Single-update atomicity gap; rollback test missing |
| Cache | Per-node channel/options state is stale until sync | Medium | Medium/High | Periodic sync and active local refresh | Propagation latency not measured |
| Retry | Retry after partial stream output duplicates client effects | Provider-dependent | High | Stream status and skip-retry controls | Cross-provider end-to-end proof missing |
| Async tasks | Two workers settle/refund same terminal transition | Low | Critical | CAS transition and DB leases | Live multi-node failure injection missing |
| Authentication | Cached token/user state briefly outlives mutation | Low/Medium | High | TTL plus targeted cache updates/invalidation | Redis race tests missing |
| Provider security | Custom base URL/proxy enables SSRF or secret forwarding | Medium | Critical | Sensitive-write permissions and protected fetch utilities | Full route-to-dialer audit not performed |
| Payments | Forged/replayed webhook credits balance | Unknown | Critical | Provider-specific handlers/tests exist | All webhook signature/idempotency paths not reviewed |
| Database | Dialect-specific migration failure | Medium | High | Explicit three-DB policy and branches | MySQL/PostgreSQL integration tests not executed here |
| Privacy | Logs retain prompts, headers or provider errors | Configuration-dependent | High | masking and admin-only fields | Deployment retention/redaction policy unknown |

## Safe change boundaries

- Low risk: additive UI display, localized labels, read-only filters, focused adapter tests.
- Medium risk: channel metadata, option settings, cache invalidation and provider request mapping.
- High risk: auth, pricing, quota, payment callbacks, migrations, retry semantics, async terminal transitions and secret-bearing overrides.
