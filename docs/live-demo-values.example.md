# PromptGate Live Demo Values Template

Create `local/live-demo.env` from this template. Do not commit the real file.

Use owner-controlled demo values only. Do not use customer data, employer data, active credentials, provider tokens as prompt content, private hiring notes, or real secrets.

```bash
# PromptGate local auth token should usually come from .env, not this file.
# PROMPTGATE_AUTH_TOKEN=

DESKTOP_APP_NAME="Cherry Studio"
# Provider-facing model. This must be a real model ID accepted by the upstream provider.
PROVIDER_MODEL="gpt-4o-mini"
# Optional explicit alias. If set, this takes precedence over PROVIDER_MODEL.
# PROMPTGATE_UPSTREAM_MODEL="gpt-4o-mini"

# Real provider route. Owner supplies these locally.
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL="https://api.provider.example/v1"
PROMPTGATE_UPSTREAM_API_KEY="owner-supplied-provider-key"
# Models exposed to desktop apps. PromptGate rewrites these to PROVIDER_MODEL upstream.
PROMPTGATE_MODEL_LIST="promptgate-live,gpt-4o-mini"

# Owner-controlled demo values.
DEMO_EMAIL="demo-alias@example.com"
DEMO_INTERNAL_IP="10.42.7.19"
DEMO_INTERNAL_DOMAIN="api.internal.demo.example"
DEMO_CODENAME="Project Raven"
DEMO_CANARY_SECRET="sk-test-abc1234567890SECRET"

# Keep this short enough to paste into a desktop app prompt.
DEMO_PROMPT_CONTEXT="PromptGate is a local-first AI DLP gateway. It scans OpenAI-compatible and Anthropic-compatible requests before provider egress, blocks secrets, and tokenizes or masks PII and internal infrastructure values."
```

Expected behavior:

- The allowed prompt forwards only rewritten placeholders upstream.
- The blocked prompt returns a local PromptGate error and creates no upstream provider request.
- `local/live-demo.env`, screenshots, MITM flows, and runtime captures stay local-only.
