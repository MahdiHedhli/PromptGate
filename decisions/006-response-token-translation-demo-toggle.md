# ADR 006: Response Token Translation Demo Toggle

## Decision

Add response token translation as an explicit demo/runtime toggle.

## Why

The public demo needs to show both provider-safe tokenized upstream traffic and optional local UX restoration. `promptgate-live` keeps translation off. `promptgate-live-translate` turns translation on while forwarding to the same configured upstream model.

## Security Posture

Translation happens only after the provider response is received, only for known scoped tokens in the current request or conversation, and never changes upstream egress. Unknown tokens and tokens from another scope are not restored. Token mappings remain in memory only and are not written to logs, status, audit events, reports, or MITM captures.

## Default

Off unless explicitly enabled by `PROMPTGATE_RESPONSE_TOKEN_TRANSLATION=true` or by selecting the `promptgate-live-translate` demo model alias.

## Tradeoff

Response token translation improves local demo clarity and desktop UX, but it expands local token-ledger risk. It remains explicit, scoped, and disabled by default.
