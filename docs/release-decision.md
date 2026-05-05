# PromptGate Release Decision

Status: Yellow pending owner real-provider visual MITM verification. Automated local gates are expected to be green.

## What Changed

- Added scoped random tokenization by default.
- Added TTL and LRU bounds for the in-memory token vault.
- Kept deterministic tokenization as explicit opt-in.
- Added global and per-rule audit-only semantics.
- Added optional local-service Privacy Filter configuration shape.
- Added ADRs and a strengthened threat model.
- Added live desktop app evidence workflow for Cherry Studio or an OpenAI-compatible fallback.
- Added `/v1/models`, `/models`, and `/chat/completions` compatibility endpoints for desktop app handshakes.
- Added live-demo scripts for preflight, stack startup/stop, allowed curl sanity check, blocked curl sanity check, and local leak assertion.
- Added explicit response token translation demo toggle with `promptgate-live` and `promptgate-live-translate`.

## What Was Ported From PromptGuard

- Token-map ledger risk framing.
- Unguessable scoped token format.
- TTL and max-conversation eviction.
- ADR discipline.
- LiteLLM hook versus gateway decision framing.
- Audit-only rollout semantics.
- MITM proof discipline.

## What Was Intentionally Not Ported

- Full PromptGuard architecture.
- Production LiteLLM CustomLogger hook.
- Automatic or default-on response restoration.
- Real Privacy Filter model runtime.
- Presidio runtime.
- LLM judge.
- Production Purview, Google SDP, Netskope, Zscaler, or Nightfall adapters.

## Known Limitations

- Real provider MITM requires owner credentials and visual verification.
- Live desktop app proof requires owner GUI actions and provider credentials.
- Cherry Studio is the primary documented target. PromptGate now supports its OpenAI-compatible streamed chat path by scanning and rewriting the request before upstream streaming. If Cherry Studio cannot route to an OpenAI-compatible base URL in the owner environment, use the documented fallback list and record why.
- Privacy Filter local service is optional and mock/test oriented unless the owner enables a real service.
- Browser ChatGPT, SaaS IDE backends, vendor-managed indexes, file/image uploads, and agentic browser actions are outside the local API gateway path.
- Response token translation is intentionally off by default and enabled only by explicit env/config or the `promptgate-live-translate` demo alias.

## Recommended Public Release Decision

Keep PromptGate as the canonical implementation. Release as a local-first MVP after owner completes the real-provider MITM visual test and chooses whether to keep the repository private or prepare a public-safe cleanup.

## Recommended Next Sprint

1. Owner-run real provider MITM verification with synthetic data.
2. Decide whether response token translation should remain demo-only or become a documented operator feature in 0.2.
3. Decide whether to prioritize a LiteLLM CustomLogger hook or keep LiteLLM downstream routing only.
