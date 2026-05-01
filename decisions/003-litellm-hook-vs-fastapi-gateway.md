# 003: LiteLLM Hook Vs FastAPI Gateway

Status: Accepted

PromptGate keeps FastAPI as the release default. The current tested LiteLLM path is:

```text
AI client -> PromptGate -> LiteLLM-compatible fake upstream
```

PromptGuard's CustomLogger hook design is useful, but PromptGate will not ship it as production-ready until it is tested against the chosen LiteLLM container and failure behavior is verified. The hook should remain provider-agnostic in PromptGate core, with any LiteLLM subclass bridge isolated under an optional Docker or deployment directory.

This keeps the MVP simple while preserving a clear future path for users who already standardize on LiteLLM.
