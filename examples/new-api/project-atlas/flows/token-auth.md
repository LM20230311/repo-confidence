# Flow: API Token Authentication

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E2-E5](../evidence.md), token masking/migration tests
> Known gaps: No end-to-end Redis-backed authentication test was executed

## Mental model

An API token is more than a key lookup. It selects a user, checks token lifecycle and IP restrictions, verifies the user is enabled, resolves the effective group, and injects quota/model constraints into Gin context for the distributor and billing system.

## Trigger and entrypoint

- Trigger: model or usage request carrying an API key.
- Entrypoint: relay routes attach `middleware.TokenAuth`.
- Supported normalization includes Bearer tokens, `x-api-key` for Claude-style requests, Gemini query/header keys, WebSocket subprotocol keys and Midjourney secrets.

## Normal path

1. Normalize the credential and remove the display `sk-` prefix.
2. `ValidateUserToken` loads token state from Redis or SQL.
3. Reject disabled, expired or exhausted tokens.
4. Enforce optional token IP/CIDR limits.
5. Load the user cache and reject disabled users.
6. Resolve token group override against the user's allowed groups and configured group ratios.
7. Put token ID, quota, model limits, group and cross-group retry flags into request context.
8. Distributor later enforces model restrictions and channel availability.

## State changes

Authentication is read-mostly. Successful SQL misses asynchronously populate Redis. Later billing changes token and user quota using atomic deltas or optional batch aggregation.

## Failure paths

| Failure | Behavior |
|---|---|
| Missing/unknown key | OpenAI-style 401 response |
| Redis miss/error | SQL fallback |
| SQL error | 500 database error rather than invalid-token masking |
| Expired/exhausted/disabled token | 401 |
| IP outside allow list | 403 |
| Disabled user or forbidden group/model | 403 |

## Security and money

- Redis token keys use an HMAC of the raw credential.
- Normal token list/get/update responses mask the key; explicit key-reveal endpoints require user ownership, critical rate limiting and cache disabling.
- Token quota is checked before billing pre-consume and adjusted with the user's funding source.

## Invariants

- A disabled user must not regain relay access through a still-valid token.
- A token must not select a group the owning user cannot use.
- Model restrictions must be checked before an upstream request.
- Token list APIs must not expose full keys by default.

## Tests

- `controller/token_test.go` verifies masking, ownership and key-column migration behavior.
- `service/authz/authz_test.go` verifies granular permission storage and reload behavior.
- Missing high-value coverage: a table-driven TokenAuth integration test spanning Redis hit, Redis failure, expiry, IP restriction and group override.
