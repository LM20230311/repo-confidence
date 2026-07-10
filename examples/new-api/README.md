# New API onboarding case

This public case applies Repo Confidence's `repository-onboarding-coach` to the open-source [QuantumNous/new-api](https://github.com/QuantumNous/new-api) repository.

> Upstream commit: [`4e570389dd433a717373ce9c9b822b59f5ed3d5d`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> Verified on: 2026-07-10
> Case status: First-pass, evidence-backed onboarding atlas
> Upstream license: [GNU AGPL v3](https://github.com/QuantumNous/new-api/blob/4e570389dd433a717373ce9c9b822b59f5ed3d5d/LICENSE)

## Purpose

The case tests whether Repo Confidence can turn a large unfamiliar repository into a compact maintenance model without generating a file-by-file encyclopedia.

It focuses on six high-value flows:

1. API token authentication and authorization;
2. synchronous model relay;
3. channel selection, retry, and automatic disablement;
4. quota pre-consume, settlement, and refund;
5. channel administration and cache refresh;
6. asynchronous media task polling and final settlement.

Start with the [Project Atlas](project-atlas/index.md).

## Verification performed

The repository was cloned read-only. The following upstream packages were executed successfully against the pinned commit:

```bash
go test ./common ./model ./service ./controller ./router ./middleware \
  ./relay ./relay/common ./relay/helper ./pkg/billingexpr -count=1
```

All ten packages passed. Frontend tests, a production-like deployment, live upstream providers, payment webhooks, and multi-node failure injection were not executed.

## How to read the case

- `Verified` means current implementation and, for high-impact claims, focused tests support the claim.
- `Partially verified` means the source path is direct but no end-to-end runtime proof was performed.
- `Inferred` means the conclusion follows from the code but still needs runtime or operational confirmation.
- `Unknown` means the current evidence is insufficient.

This is an independent learning artifact, not official New API documentation, a security audit, or an endorsement by the upstream maintainers. No upstream source code is vendored here.
