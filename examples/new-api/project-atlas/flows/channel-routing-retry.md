# Flow: Channel Selection, Retry and Automatic Disablement

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E5, E8, E9, E15](../evidence.md)
> Known gaps: No direct priority/weight statistical test or live failure injection was found

## Mental model

Routing is two-dimensional: group/model eligibility determines the candidates, priority determines the failover tier, and weight randomizes selection within that tier. Retry advances through priority levels and may traverse configured auto groups. Optional affinity can choose a previous channel before normal selection.

## Normal path

1. `Channel` mutations maintain denormalized `Ability` rows for every group/model pair.
2. `InitChannelCache` loads channels and abilities, filters disabled channels and sorts candidate IDs by descending priority.
3. Distributor checks a channel-affinity rule; a valid enabled preferred channel wins.
4. Otherwise `GetRandomSatisfiedChannel` selects the priority corresponding to the retry index.
5. Within that priority, a weighted random choice selects the channel.
6. `SetupContextForSelectedChannel` chooses an enabled key, loads base URL, mappings, overrides and provider-specific settings.
7. On a retry, `CacheGetRandomSatisfiedChannel` advances priority and optionally auto group.

## Multi-key behavior

A channel can hold multiple keys. Random or polling key selection occurs inside the selected channel. Per-key status maps allow one failing key to be disabled without immediately removing the whole channel; the channel becomes auto-disabled when no enabled key remains.

## Retry decision

Retry stops when:

- the error is marked skip-retry;
- the configured retry budget is exhausted;
- a specific channel was explicitly requested;
- channel-affinity policy says failure should stay sticky;
- operation settings exclude the error/status code;
- the response status indicates success.

Otherwise configured retryable status codes, channel errors and invalid status codes can advance to another candidate.

## Automatic disablement and recovery

`processChannelError` delegates health decisions to `service.ShouldDisableChannel`. When automatic disablement and channel auto-ban are enabled, the selected key/channel status is changed asynchronously and routing abilities are disabled. Scheduled channel tests provide passive recovery for auto-disabled channels; manually disabled channels are excluded from that recovery mode.

## Invariants

- Lower priority must not receive traffic while a usable higher-priority tier is selected for the same retry stage.
- A disabled channel or key must not remain an eligible candidate after cache convergence.
- Manual disablement must not be silently reversed by passive automatic recovery.
- Credential/header/model overrides must belong to the channel actually used for that attempt.

## Tests and gaps

- Affinity template, cache clearing and retry-suppression behavior have focused service tests.
- Channel test selection verifies passive recovery only targets auto-disabled channels.
- Missing high-value coverage: deterministic tests for priority advancement, weight boundaries, cache/DB parity, multi-key exhaustion and cross-group retry.
