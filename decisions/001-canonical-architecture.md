# 001: Canonical Architecture

Status: Accepted

PromptGate remains the canonical product and repository. PromptGuard is treated as a read-only donor spike for architecture lessons, not as a codebase to merge wholesale.

PromptGate keeps the clone-and-run FastAPI gateway as the default path:

```text
AI client -> PromptGate FastAPI gateway -> mock, fake, LiteLLM, or explicit upstream provider
```

This path is already tested locally without external credentials and is easier for a user to inspect than a provider-specific hook. Optional integrations can wrap or sit behind this gateway, but they must not break the default local gateway flow.

Tradeoff: a LiteLLM pre-call hook can be cleaner inside a LiteLLM-first deployment, but it adds runtime coupling and container complexity. PromptGate will document that hook path as future/optional until it is tested end to end with the selected LiteLLM deployment.
