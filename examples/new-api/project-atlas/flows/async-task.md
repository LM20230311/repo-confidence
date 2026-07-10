# Flow: Asynchronous Media Task and Final Settlement

> Status: Verified for selected backend behavior
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E1, E2, E13](../evidence.md), task polling/CAS/billing/system-task tests
> Known gaps: Live provider polling and process-crash recovery were not executed

## Mental model

Media generation is a two-phase workflow. The submit request reserves full quota, sends the job to a provider and stores a local task plus billing snapshot. A DB-leased system task later polls unfinished jobs. Only the poller that wins the terminal CAS transition may settle success or refund failure.

## Submit path

1. Token authentication and distribution select a channel.
2. Resolve remix/origin task when applicable and lock it to the original channel.
3. Choose a `TaskAdaptor` and validate provider-specific request fields.
4. Apply model mapping and generate a public `task_*` ID.
5. Calculate per-call price and bounded duration/resolution multipliers.
6. Force full pre-consume; retry attempts reuse the same BillingSession.
7. Submit upstream and optionally adjust quota from the provider response.
8. Settle the submit delta and write a task-consumption log.
9. Insert the task with upstream ID, funding source, token ID, node and billing snapshot.

## Polling path

1. Scheduled `async_task_poll` work is deduplicated through the system-task runner.
2. Query unfinished tasks, group them by platform and channel, and poll channels concurrently.
3. Parse provider status and redact large embedded media from stored responses.
4. Update non-terminal progress with a status guard.
5. On success/failure, attempt `Task.UpdateWithStatus(previousStatus)`.
6. Only the CAS winner performs terminal billing.
7. Success may apply adaptor-specific or token-based final settlement.
8. Failure and non-legacy timeout refund the stored quota.

## State changes

| State | Submit | Terminal poll |
|---|---|---|
| Wallet/subscription | Full pre-consume and submit delta | Final delta or refund |
| Token quota | Full pre-consume and submit delta | Final delta or refund |
| `tasks` | Insert IDs, status, private billing snapshot | CAS status, result URL, reason, final quota |
| Logs | Initial task consumption | Adjustment/refund log |
| System task | Scheduled/claimed with renewable lease | Success/failure history |

## Failure paths

- Submit validation and local errors do not retry.
- Retryable provider errors can select another channel, except remix paths locked to the original channel.
- Missing channel during polling marks tasks failed; exact refund behavior for every bulk-failure path needs further verification.
- Timed-out legacy tasks are failed without automatic refund; newer tasks refund after winning CAS.
- Polling returns on 429/temporary provider conditions without forcing failure in selected paths.

## Invariants

- Async requests must pre-consume full quota before returning a task ID.
- Public task IDs and upstream IDs must remain distinct.
- Provider keys and private result metadata must not be returned to users.
- Exactly one terminal transition may settle or refund.
- Final settlement must use the submission-time model/group/multiplier snapshot where available.

## Tests

- `model/task_cas_test.go` verifies winning, losing and concurrent CAS transitions.
- `service/task_billing_test.go` verifies wallet/subscription refunds, positive/negative deltas and CAS-guarded settlement.
- `service/task_polling_test.go` verifies per-channel polling delays do not block other channels.
- `model/system_task_test.go` and `service/system_task_test.go` verify active-key deduplication, leases and scheduler behavior.
