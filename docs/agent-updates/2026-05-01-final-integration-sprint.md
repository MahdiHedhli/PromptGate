# PromptGate Final Integration Sprint: 2026-05-01

## Status

Yellow pending owner real-provider MITM verification. Local automated gates are green so far on `feature/final-integration-sprint`.

## What Changed

- Added ADRs under `decisions/`.
- Added `docs/threat-model.md`, `docs/integration-plan.md`, `docs/release-decision.md`, and `docs/benchmarks.md`.
- Added scoped random tokenization as the default policy mode.
- Added TTL and LRU eviction for the in-memory token vault.
- Kept deterministic tokenization as explicit opt-in for demos and reproducible tests.
- Added global and per-rule audit-only semantics.
- Added sanitized policy hash and optional confidence fields to audit events.
- Added an optional Privacy Filter local-service configuration path with mocked HTTP tests.
- Updated MITM, policy schema, operations, LiteLLM, README, and blog evidence docs.

## What Was Ported From PromptGuard

- ADR discipline.
- Token-map ledger risk framing.
- Unguessable per-conversation token IDs.
- TTL and max-conversation eviction.
- Audit-only rollout semantics.
- LiteLLM hook versus FastAPI gateway decision framing.
- MITM evidence discipline.

## What Was Intentionally Not Ported

- Wholesale PromptGuard architecture.
- Production LiteLLM CustomLogger hook.
- Response token restoration.
- Real Privacy Filter model runtime or model downloads.
- Presidio runtime.
- LLM judge.
- Production enterprise DLP vendor adapters.

## Commands Run

| Command | Result |
|---|---:|
| `.venv/bin/python -m pytest -q` | pass, 50 tests |
| `./scripts/test-egress.sh` | pass |
| `./scripts/release-check.sh` | pass before final doc/report updates |

## Owner-Only Verification

- Run the real-provider MITM path in `docs/MITM_VERIFICATION.md` with synthetic data only.
- Decide whether response token restoration is required for a later release.
- Decide whether LiteLLM CustomLogger hook work is worth prioritizing over the simpler tested downstream route.

## Risks And Limitations

- Real Privacy Filter service execution is not claimed in this branch.
- Browser ChatGPT, SaaS IDE backends, vendor-managed indexes, file/image uploads, and agentic browser actions remain outside PromptGate's local API gateway scope.
- Scoped random tokens improve guessing resistance but tokenization still creates an in-memory sensitive ledger.
