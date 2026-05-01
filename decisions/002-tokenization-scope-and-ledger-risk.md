# 002: Tokenization Scope And Ledger Risk

Status: Accepted

PromptGuard's strongest security lesson is that reversible tokenization creates a sensitive ledger. Even if raw prompt values never leave the host, a token map that can restore `[CATEGORY_token]` back to raw text is itself sensitive.

PromptGate now defaults to scoped random tokenization:

```yaml
tokenization:
  mode: scoped_random
  ttl_seconds: 3600
  max_conversations: 100
  restore_responses: false
```

The default token format uses an unguessable 16-hex suffix such as `[PRIVATE_EMAIL_a3f9c1d2e4b56789]`. The same raw value maps to the same token within a conversation, but different conversations receive different tokens. The map is in-memory only, evicted by TTL and LRU limits, and is not emitted in status, logs, reports, or audit events.

Deterministic sequential tokens remain available for reproducible demos and tests, but they are explicit opt-in because they are easier for an LLM response to guess.

PromptGate does not restore response tokens by default. Response restoration remains a future path because it increases prompt-injection and ledger-risk complexity.
