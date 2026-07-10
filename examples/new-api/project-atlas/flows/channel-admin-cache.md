# Flow: Channel Administration and Runtime Cache Refresh

> Status: Verified for selected backend behavior
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E12, E15](../evidence.md), channel permission tests
> Known gaps: Multi-node propagation latency was not measured

## Mental model

An operator mutation changes both the provider account (`Channel`) and its routing index (`Ability`), then refreshes process-local channel and HTTP-client state. The route layer separates read, operate, write and sensitive-write permissions.

## Preconditions

- Session or management access-token authentication with admin role.
- Granular Casbin permission for the operation.
- Sensitive fields such as key, base URL, type and header override require sensitive-write permission.
- Explicit key-reveal requires root, secure verification, rate limiting and disabled response caching.

## Create

1. Validate channel shape and selected creation mode.
2. Normalize one key, a batch of single-key channels, or one multi-key channel.
3. `BatchInsertChannels` writes channel rows and derived abilities in one transaction.
4. Reset proxy-client cache and record a management audit.

## Update

1. Reject direct status mutation through the general update route.
2. Remove read-only accounting fields from the patch.
3. Load the existing channel and preserve multi-key state.
4. Classify sensitive changes and fail closed for unknown fields.
5. Update channel data and rebuild its abilities.
6. Reinitialize the channel cache and reset proxy-client cache.
7. Record changed field names without recording secret contents.

## Status and delete

- Status changes use dedicated operate-permission routes and only accept enabled/manual-disabled states.
- Automatic disablement can set an auto-disabled state internally.
- Delete removes the channel and abilities, refreshes routing cache and writes an audit record.

## State changes

| State | Change |
|---|---|
| `channels` | Credential, endpoint, models, groups, priority, weight and status |
| `abilities` | Rebuilt group/model/channel eligibility rows |
| channel cache | Full process-local rebuild after controller mutations |
| proxy client cache | Reset after connection-affecting mutations |
| audit log | Operation and non-secret change summary |

## Invariants

- Every mutable channel field must be classified as sensitive, non-sensitive, operational or read-only.
- Secrets must never appear in management audit details or normal list responses.
- Channel and Ability eligibility must converge before new traffic relies on the mutation.
- Status mutation must not bypass the dedicated permission and state validation.

## Atomicity boundary

Batch creation and batch deletion use transactions. A single `Channel.Update` writes the channel before rebuilding abilities in a separate transaction; a failure during ability rebuild can leave the two representations inconsistent until repaired. The project exposes `FixAbility`, but this case did not reproduce that failure.

## Tests

`controller/channel_authz_test.go` protects sensitive-field classification, read-only fields and status handling. `router/channel_router_test.go` protects permission assignment for status and deletion routes. Direct cache propagation and Channel/Ability rollback behavior lack focused end-to-end coverage in this case.
