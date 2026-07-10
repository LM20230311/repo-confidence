# Change Brief: Token-specific Billing Multiplier

> [中文版本](token-billing-multiplier.zh-CN.md)

> Prepared against commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Risk: High
> Status: Analysis only; no upstream implementation

## Goal and acceptance criteria

Add an optional multiplier to an API token so two tokens owned by the same user
can be charged differently without changing model or group price configuration.

Acceptance criteria:

- existing tokens behave exactly as multiplier `1`;
- the configured multiplier is validated, bounded and cannot be NaN or infinite;
- the multiplier applies exactly once to the complete billable amount;
- legacy ratio, fixed-price, tiered-expression, audio and async-task paths agree;
- pre-consume and actual settlement use the same request-start value;
- changing a token later does not reprice an in-flight request or task;
- wallet/subscription quota and token quota settle the same final amount;
- usage logs retain the multiplier and effective final quota;
- overflow uses the existing checked saturation and audit path.

Out of scope:

- replacing model, completion, cache or group ratios;
- changing channel selection;
- introducing a new currency or payment provider;
- implementing the change in the upstream New API repository.

## Current behavior and evidence

### Token persistence and cache — Verified

`model.Token` stores quota, model limits, IP limits, group and cross-group retry,
but no price adjustment. `AddToken`, `UpdateToken` and `Token.Update` explicitly
copy/select supported fields. Redis stores the token object under a keyed-HMAC
cache key. Authentication copies selected fields into Gin context, then
`RelayInfo` carries them through the request. See [E18](../evidence.md).

### Pricing — Verified

`PriceData` contains model, completion, cache, image, audio and group ratios,
plus provider/request-specific `otherRatios`. Ratio, fixed-price and tiered
modes have different pre-consume and actual-settlement code paths. Audio and
task billing also have specialized paths. See [E10, E11 and E19](../evidence.md).

### Async tasks — Verified

`TaskBillingContext` persists model price, model ratio, group ratio and
`otherRatios`, allowing polling to settle after the original request has ended.
It currently has no generic commercial multiplier snapshot. See [E20](../evidence.md).

## Proposed semantic contract

Use one explicit final multiplier:

```text
base quota = model/component pricing + billable surcharges
commercial quota = base quota × token billing multiplier
```

Rules:

- default is exactly `1`;
- `0` does not mean free; free behavior remains an explicit pricing decision;
- decide a bounded product range, for example `(0, 1000]`;
- apply after component-specific and provider/request-specific calculations;
- perform one checked Decimal-to-quota conversion at the final boundary;
- persist the request-start multiplier as a decimal string or equivalent exact snapshot.

The exact upper bound and whether normal users may edit their own multiplier
are product decisions. They block implementation because they change abuse and
commercial risk.

## Expected impact

| Area | Impact | Evidence |
|---|---|---|
| Token schema | Add multiplier with backward-compatible default | `model.Token`, auto-migration |
| Token API | Create/update validation, masked responses and permissions | `controller/token.go`, token tests |
| Redis token cache | Cached token object carries new value; mutation refreshes cache | `model/token_cache.go` |
| Request context | Copy validated value into context and `RelayInfo` | `SetupContextForToken`, `GenRelayInfo` |
| Price snapshot | Add a named commercial multiplier, not an anonymous provider ratio | `PriceData`, `BillingSnapshot` |
| Ratio/fixed settlement | Multiply the final amount once | `service/text_quota.go` |
| Tiered settlement | Freeze and apply multiplier after expression plus surcharge composition | `service/tiered_settle.go`, `composeTieredTextQuota` |
| Audio/realtime | Apply through the same final helper | `service/quota.go` |
| Async tasks | Persist in `TaskBillingContext`; reuse during completion adjustment | `model/task.go`, `service/task_billing.go` |
| BillingSession | No price-policy change; receives multiplied final quota | `service/billing_session.go` |
| Logs/UI | Record token multiplier, base quota and effective quota | log generators and usage-log UI |
| Compatibility | Existing rows and old task snapshots default to `1` | migration and snapshot readers |

## Why `otherRatios["token"]` is not sufficient

That shortcut is attractive because `PriceData` already multiplies
`otherRatios` in normal text settlement. It is incomplete:

1. tiered expression settlement bypasses `ApplyOtherRatiosToDecimal`;
2. audio settlement uses separate formulas;
3. async adaptors may call `ReplaceOtherRatios`, losing a token entry;
4. the map represents request/provider dimensions such as duration, size and `n`;
5. logs and historical audits would not have a stable commercial field.

This is a high-impact example of why similar-looking data structures do not
necessarily share the same business semantics.

## Implementation outline

### 1. Define and validate the persisted value

- Add a token multiplier field with a database default equivalent to `1`.
- Update token creation, update selection and response construction explicitly.
- Reject missing authorization, non-positive values, NaN/infinity and values above the product bound.
- Decide whether only administrators can set it; do not infer this from token ownership.
- Verify SQLite, MySQL and PostgreSQL migration behavior.

### 2. Create request-local immutable state

- Add the value to token authentication context.
- Copy it into `RelayInfo` once.
- Normalize old/empty values to `1` at this boundary.
- Never re-read the token row during settlement to obtain a newer multiplier.

### 3. Introduce one named application helper

Create a helper with semantics equivalent to:

```text
ApplyCommercialMultiplier(base decimal, snapshot multiplier)
→ checked, saturated integer quota + audit marker
```

Do not apply it in `BillingSession`; the session should remain unaware of how
price was constructed.

### 4. Integrate every price mode

- Multiply the pre-consume estimate for ratio and fixed-price requests.
- Add the multiplier to the tiered billing snapshot and apply it during both estimate and actual settlement.
- Apply it after tool/search/image/audio surcharges according to the semantic contract.
- Route audio, realtime and other specialized quota calculations through the same final helper.
- Confirm free and zero-usage behavior explicitly.

### 5. Persist async snapshots

- Add the multiplier to `TaskBillingContext`.
- Default old snapshots to `1`.
- Ensure submit-time adjustment and completion-time recalculation apply it once.
- Prevent adaptor `ReplaceOtherRatios` calls from altering the commercial multiplier.

### 6. Make charges explainable

Record at least:

- base quota before the token multiplier;
- token multiplier snapshot;
- final quota;
- price mode and existing model/group dimensions;
- saturation marker when applicable.

Historical logs must not depend on the token's current value.

## Failure and concurrency analysis

- A token update racing with a request uses whichever value authentication loaded; settlement must keep that snapshot.
- Redis may briefly serve the old token value after an update; this follows existing token-cache consistency and should be tested/documented.
- A multiplier increase may make pre-consume exceed wallet, subscription or token quota; rejection must happen before upstream work when estimable.
- A multiplier overflow must saturate visibly, never wrap into a negative charge.
- A process crash during refund remains an existing durability gap and is not solved by the multiplier.
- Async tasks created before deployment must interpret absent snapshot fields as `1`.

## Invariants

- The multiplier is applied exactly once.
- Pre-consume and settlement use one immutable multiplier snapshot.
- Token quota and selected funding source move by the same effective quota.
- A multiplier change never rewrites historical billing semantics.
- Provider-specific ratios cannot erase or replace the token multiplier.
- Default behavior remains bit-for-bit compatible where rounding permits.

## Verification plan

### Calculation matrix

Test multipliers `0.5`, `1`, `2` and the configured maximum against:

- legacy text with input/output/cache dimensions;
- fixed-price request;
- tiered expression with a tier crossing;
- tool/search surcharge;
- audio input/output;
- async per-call task;
- async task recalculated from actual duration or tokens.

### Lifecycle matrix

- wallet and subscription funding;
- insufficient pre-consume quota;
- actual quota above/below estimate;
- upstream failure and refund;
- duplicate settle/refund calls;
- token update between pre-consume and settlement;
- process restart before async task completion;
- Redis hit, miss and stale-value window.

### Compatibility and audit

- migrate existing rows on all supported databases;
- read old task snapshots without the field;
- assert logs include base, multiplier and final quota;
- assert saturation is visible in admin metadata;
- assert ordinary model/group pricing is unchanged at multiplier `1`.

## Rollout and rollback

1. Deploy schema and snapshot readers that default to `1`.
2. Add shadow calculation and compare old/new quota without charging the new value.
3. Enable administrator-only configuration behind a feature flag.
4. Compare pre-consume, settlement and log reconciliation by price mode.
5. Enable a small set of tokens before general availability.

Rollback must stop new multiplier application while retaining the field and
snapshot readers until all in-flight async tasks created under the new contract
have reached terminal state.

## Unknowns and decisions

| Question | Impact | Blocking | Verification/owner |
|---|---|---:|---|
| Who may set the multiplier? | Prevents users discounting themselves | Yes | Product/security decision |
| Is it allowed below `1`? | Defines discount semantics | Yes | Commercial decision |
| Which surcharges are multiplied? | Changes final revenue | Yes | Explicit billing contract |
| What numeric range/precision is required? | Storage and overflow behavior | Yes | Finance/engineering decision |
| Should subscription plan limits use pre- or post-multiplier quota? | Changes entitlement consumption | Yes | Product decision |
| Does violation fee inherit the multiplier? | Abuse economics | Yes | Security/product decision |

## Risk rating

High. The change touches authentication-derived state, database migration,
Redis cache, every pricing mode, wallet/subscription balances, token quota,
async snapshots and financial audit. Fast implementation would not reduce that
risk.
