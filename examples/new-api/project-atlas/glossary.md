# Glossary

> Status: Partially verified
> Last verified commit: [`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Evidence: [E3-E15](evidence.md)
> Known gaps: Product-language nuances may differ from operator terminology

| Term | Business meaning | Code representation | Source of truth | Common confusion |
|---|---|---|---|---|
| User | Human or account that owns quota, tokens and settings | `model.User` | `users` | Dashboard access token is not the same as an API token |
| Token | API credential with quota, IP, group and model limits | `model.Token` | `tokens` | Displayed `sk-` prefix is normalized before lookup |
| Group | Pricing and channel-access segment | user/token context plus ratio settings | `options` and entity fields | Token group can override the user's default group |
| Channel | Configured upstream provider account or endpoint | `model.Channel` | `channels` | One channel may hold multiple keys and many models |
| Ability | Search index connecting group, model and channel | `model.Ability` | `abilities` | It duplicates priority/weight/status for routing performance |
| Channel priority | Ordered failover tier | `Channel.Priority`, `Ability.Priority` | SQL and channel cache | Higher priority is selected before lower priority |
| Channel weight | Random distribution within a priority | `Channel.Weight`, `Ability.Weight` | SQL and channel cache | Weight does not override priority |
| Affinity | Optional rule that keeps related requests on one channel | `service.channelAffinityCache` | Redis or local LRU | It may suppress retry depending on rule settings |
| RelayInfo | Request-scoped control object | `relay/common.RelayInfo` | Built from Gin context | It carries identity, pricing, retry and provider metadata |
| Adaptor | Provider protocol translation and I/O interface | `relay/channel.Adaptor` | Code | Channel type and API type are related but distinct |
| PriceData | Fixed price/ratio inputs and estimated quota | `types.PriceData` | Runtime snapshot from settings | It is not itself the durable billing record |
| BillingSession | Pre-consume, settle and refund lifecycle | `service.BillingSession` | Request memory plus durable balance writes | Funding can be wallet or subscription |
| Quota | Internal accounting unit | integer user/token/log fields | SQL with optional Redis/batch deltas | It is not necessarily a display currency |
| Tiered expression | Self-contained price expression using actual token categories | `pkg/billingexpr` | `options` maps | Its coefficients are real prices, not legacy ratios |
| Task | Long-running media generation job | `model.Task` | `tasks` | Public task ID differs from the upstream task ID |
| SystemTask | DB-leased background operation | `model.SystemTask` | system-task tables | It schedules polling; it is not the media task itself |
| Option | Dynamic global configuration key/value | `model.Option` | `options` | Runtime code reads a synchronized in-memory map |
