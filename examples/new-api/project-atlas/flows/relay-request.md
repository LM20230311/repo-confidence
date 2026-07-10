# Flow: Synchronous Model Relay

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E2, E5-E11](../evidence.md)
> Known gaps: No live provider or end-to-end streaming request was executed

## Mental model

The relay controller owns the request transaction: validate a client protocol, estimate usage and price, reserve quota, try one or more channels, let the selected adaptor translate and call the provider, settle actual usage, and return the provider-compatible response.

## Trigger and entrypoint

- OpenAI-compatible: `/v1/chat/completions`, `/v1/responses`, embeddings, image, audio, rerank and realtime routes.
- Claude-compatible: `/v1/messages`.
- Gemini-compatible: `/v1beta/models/*path`.
- Router chain: performance check → TokenAuth → model rate limit → Distributor → `controller.Relay`.

## Normal path

1. Distributor extracts the requested model, enforces token model limits and selects an initial channel.
2. `controller.Relay` validates the protocol-specific request.
3. `RelayInfo` captures user, token, group, model, retry and request metadata.
4. Sensitive-text checks and token estimation run when configured.
5. `ModelPriceHelper` freezes price inputs and computes pre-consume quota.
6. `BillingSession` reserves token quota and wallet/subscription funding.
7. The controller enters a bounded retry loop and refreshes selected-channel context per attempt.
8. A protocol helper creates the selected provider adaptor, maps model/request fields and sends the upstream request.
9. The adaptor normalizes the response and usage.
10. Text/audio/image-specific settlement computes actual quota, updates accounting and writes a consumption log.

## State changes

| State | Mutation |
|---|---|
| Wallet/subscription | Pre-consume, then delta settle or refund |
| Token quota | Pre-consume, then delta settle or refund |
| Channel health | Error may disable a key or channel asynchronously |
| Usage/log state | Consumption/error record plus aggregate counters |
| Affinity | Successful channel may be cached for related requests |

## Failure paths

- Validation, pricing and permission errors are marked skip-retry.
- Request bodies are stored and reopened for each retry; oversized bodies map to 413.
- Provider failures are normalized and checked against configured retry status codes.
- Failure after pre-consume calls `BillingSession.Refund` unless the session has already settled.
- Error logs include request and channel metadata; sensitive fields are masked or admin-only.

## Streaming boundary

The code has stream-status tracking and provider-specific stream scanners, but this case did not prove every provider's behavior after the first response chunk. Treat changes to retry-after-output and usage extraction as high risk.

## Invariants

- The same request body must be replayable across retries.
- Pricing and funding decisions must be made before the upstream request.
- Actual usage must settle against the same request's billing snapshot.
- A failed request must not retain an unsettled pre-consume without an explicit violation fee.
- Client-visible protocol format must match the requested relay format.

## Tests

Selected `relay`, `relay/common`, `relay/helper`, `service` and `pkg/billingexpr` packages passed. Provider-specific coverage exists for OpenAI, Claude, Gemini, AWS, Moonshot, MiniMax, Ollama and task adaptors, but this case did not execute every adaptor package.
