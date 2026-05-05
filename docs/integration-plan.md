# Final Integration Plan

PromptGate is the canonical repository. PromptGuard is a donor spike used for security and architecture lessons.

## Ported In This Sprint

- ADR structure for durable security decisions.
- Threat-model language for token-map ledger risk and prompt-injection restoration risk.
- Scoped random tokenization with TTL and LRU conversation eviction.
- Deterministic tokenization as explicit opt-in.
- Global and per-rule audit-only semantics.
- Optional Privacy Filter local-service configuration shape.

## Intentionally Not Ported

- PromptGuard wholesale architecture.
- Production LiteLLM CustomLogger hook.
- Default-on or automatic response token restoration. PromptGate now has explicit response token translation for demos and controlled runtime use.
- Real model downloads for OpenAI Privacy Filter.
- Presidio runtime dependency.
- LLM judge path.
- Production vendor DLP adapters.

## Release Decision Criteria

Keep PromptGate if local clone-and-run quickstart, fake egress proof, fake upstream, LiteLLM route shape, MITM fake-upstream proof, auth, policy validation, and leak assertions remain green.

Revisit PromptGuard-only ideas only if the owner chooses a LiteLLM-first deployment or broader response token translation becomes a hard requirement.
