# Flow: Quota Pre-consume, Settlement and Refund

> Status: Verified for selected backend behavior
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E10, E11, E13](../evidence.md), executed quota/billing tests
> Known gaps: Crash durability and production reconciliation were not tested

## Mental model

Billing is a request lifecycle, not a logging side effect. The system resolves a price model and funding preference, creates one `BillingSession`, pre-consumes both token quota and wallet/subscription funding, then settles the delta from actual usage or refunds on failure.

## Pricing modes

| Mode | Input | Settlement basis |
|---|---|---|
| Ratio | Model, completion, cache, image, audio and group ratios | Actual normalized usage × ratios |
| Fixed/per-call | Model price plus optional task multipliers | Request/task amount |
| Tiered expression | Versioned expression with token/request variables | Frozen expression rerun with actual usage |

Tiered expressions store a snapshot containing expression text/hash/version, group ratio, estimated token counts and quota conversion. Settlement uses the frozen request input rather than current settings.

## Normal path

1. Estimate request tokens and output bounds.
2. Resolve model price/ratio, group ratio and specialized ratios.
3. Create `BillingSession` using `subscription_only`, `wallet_only`, `wallet_first` or `subscription_first` preference.
4. Pre-consume token quota.
5. Pre-consume the chosen funding source; roll back token quota if funding fails.
6. Call upstream.
7. Normalize actual usage, including cache/image/audio categories.
8. Compute actual quota from the frozen price context.
9. Settle `actual - preConsumed` against funding and token quota.
10. Write consumption and audit details, including saturation markers.

## Failure and compensation

- Before funding succeeds: completed token reservation is rolled back.
- After pre-consume but before settlement: deferred error handling calls `Refund`.
- `BillingSession` protects duplicate settle/refund calls with a mutex and state flags.
- Subscription refunds use request-ID-backed durable pre-consume records and retry.
- Wallet refunds are additive and intentionally not retried because a duplicate would over-credit.
- If funding settles but token adjustment fails, the session is marked settled and logs the token failure rather than refunding already-committed funding.

## Safety controls

- Negative quota inputs are rejected.
- User-controlled multipliers are bounded before calculation.
- Quota conversions use saturating helpers rather than unchecked float-to-int casts.
- NaN, infinity and non-positive task ratios are filtered.
- Saturation is attached to admin-visible log metadata.
- Async tasks force full pre-consume and cannot use the trust-quota bypass.

## Invariants

- Pre-consume and settlement must use one frozen price contract.
- A request must not produce a negative charge from overflow or invalid multipliers.
- Wallet/subscription and token quota must move in the same direction for a successful settlement.
- A failed request must refund at most once within a live session.
- Subscription pre-consume must be idempotently identifiable by request ID.

## Tests

Executed packages cover quota saturation, expression compilation and tiers, cache-token normalization, group scaling, frozen request input, task positive/negative delta, task refunds and CAS-guarded settlement. No production ledger reconciliation or crash-injection test was run.
