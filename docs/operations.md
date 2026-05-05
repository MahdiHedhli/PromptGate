# Operations

## Local Auth

PromptGate requires `PROMPTGATE_AUTH_TOKEN` by default. Generate one with:

```bash
./scripts/setup-local-key.sh
```

Unsafe unauthenticated mode exists only for local development:

```bash
PROMPTGATE_UNSAFE_DEV_NO_AUTH=true
```

Do not use unsafe mode for demos involving real tools.

## Doctor

```bash
./scripts/doctor.sh
promptgate doctor
```

Doctor checks policy validity, auth mode, provider mode, upstream config, raw prompt logging, and port availability. It redacts API keys.

## Streaming

PromptGate 0.1.0 supports OpenAI-compatible `stream=true` for `/v1/chat/completions`. Requests are authenticated, scanned, policy-evaluated, and rewritten before the upstream stream is opened. Blocked requests return a local error and do not create an upstream request. Response token translation is disabled by default, but can be enabled explicitly with `PROMPTGATE_RESPONSE_TOKEN_TRANSLATION=true` or the `promptgate-live-translate` demo model alias.

## Tokenization

Default tokenization is scoped random:

```yaml
tokenization:
  mode: scoped_random
  ttl_seconds: 3600
  max_conversations: 100
  restore_responses: false
```

Token mappings are in-memory only, scoped by conversation/request ID, and evicted by TTL and LRU limits. They are not written to status, logs, reports, or audit events. `deterministic` mode is available for reproducible demos and tests, but it is opt-in.

When response token translation is enabled, PromptGate translates only known scoped tokens in the provider response after upstream receipt. It does not change upstream requests, and unknown or cross-scope tokens are not restored.

## Audit-Only Rollout

Set `mode: audit`, `audit_only: true`, or per-rule `audit_only: true` to observe findings without blocking or rewriting. Audit-only events are sanitized metadata only.

## Upstream Modes

Default:

```bash
PROMPTGATE_PROVIDER_MODE=mock
```

Direct fake or real upstream, when explicitly configured:

```bash
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL=http://127.0.0.1:8791
PROMPTGATE_UPSTREAM_API_KEY=<key>
```

Real provider tests require owner-supplied credentials.

Optional MITM/proxy settings:

```bash
PROMPTGATE_UPSTREAM_HTTP_PROXY=http://127.0.0.1:8080
PROMPTGATE_UPSTREAM_CA_BUNDLE=<path to mitmproxy CA bundle>
```

These settings are disabled by default and are intended for owner-controlled verification or controlled network environments.
