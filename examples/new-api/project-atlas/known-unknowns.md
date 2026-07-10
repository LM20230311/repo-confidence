# Known Unknowns

> Status: Active register
> Last reviewed commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)

| Question | Why it matters | Current evidence | Cheapest safe verification | Blocking? |
|---|---|---|---|---|
| Can every stream adaptor prevent retry after visible output? | Duplicate/malformed client responses | Stream tracking exists; no cross-provider proof | Inject failure after first chunk in OpenAI/Claude/Gemini tests | Yes for retry changes |
| How are wallet refunds recovered if the process dies before/inside the async refund goroutine? | User may remain overcharged | Refund is in-process and additive | Add crash-recovery design review and fault-injection test | Yes for billing changes |
| Are batch quota deltas flushed on graceful shutdown? | SQL balances may lag or lose deltas | No shutdown call to `batchUpdate` found | Enable batch mode, terminate around flush boundary, inspect SQL | Yes for enabling batch mode broadly |
| Can `Channel.Update` leave abilities stale when rebuilding abilities fails? | Wrong routing after admin change | Channel write precedes separate ability transaction | Force ability write failure and inspect rollback state | Yes for channel schema changes |
| Which payment webhooks have complete signature and replay protection? | Direct financial loss | Handlers and some tests exist; not reviewed end to end | Build provider-by-provider webhook matrix | Yes for payment operations |
| What is the supported production Go version? | Contributor build reproducibility | `go.mod` says 1.25.1; Docker builder uses 1.26.1; policy text says 1.22+ | Confirm release CI/toolchain policy with maintainers | No for reading; yes for build changes |
| Why is `VERSION` empty at the analyzed commit? | Build/version metadata may differ by release pipeline | File is empty in this checkout | Inspect release workflow/tag checkout behavior | No |
| What log fields and retention are used in production? | Privacy, compliance and incident response | Code supports main DB or ClickHouse and masks selected fields | Inspect deployment options and sample redacted logs | Yes for privacy claims |
| What are the expected cache consistency SLOs in multi-node deployments? | Permission/routing change propagation | Periodic sync defaults to 60s | Run two-node mutation/observation test | Yes for strict revocation claims |
| Which provider adaptors are considered production-supported versus compatibility-only? | Maintenance scope and testing priority | Large adaptor registry, uneven tests | Use release docs and maintainer confirmation | No for core navigation |
