# PromptGate

Local-first AI DLP for prompts, tools, and model context.

PromptGate is a clone-and-run proof of concept gateway that sits between API/CLI AI tools and an upstream model provider. It scans request payloads before provider egress, applies policy-as-code, blocks secrets by default, and masks or tokenizes sensitive values before they can leave the machine.

## Quickstart

```bash
cp .env.example .env
./scripts/setup-local-key.sh
./scripts/init-policy.sh security_consulting
python3.12 -m venv .venv || python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
set -a; source .env; set +a
.venv/bin/python -m uvicorn promptgate.server:app --host 127.0.0.1 --port 8787
./scripts/test-egress.sh
```

Docker path:

```bash
cp .env.example .env
./scripts/init-policy.sh security_consulting
docker compose up -d
./scripts/test-egress.sh
```

## Client Examples

Claude Code-style local override:

```bash
export ANTHROPIC_AUTH_TOKEN=local_promptgate_key
export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
```

OpenAI-compatible request:

```bash
curl -s http://127.0.0.1:8787/v1/chat/completions \
  -H "Authorization: Bearer local_promptgate_key" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Email alice@example.com"}]}'
```

## What It Covers

- API/CLI model traffic routed through `127.0.0.1`.
- OpenAI-compatible `/v1/chat/completions`.
- Anthropic-compatible `/v1/messages` for local proxy experiments.
- Nested text fields including system/developer content, tool output, content blocks, prompts, and arguments.
- Local regex, secret, custom keyword, sample DLP import, and adversarial normalization scanners.
- Optional Privacy Filter scanner interface with a mock provider for tests.

## What It Does Not Cover

PromptGate does not automatically intercept browser ChatGPT, SaaS IDE traffic, centralized enterprise proxy traffic, or vendor-managed code indexes. Those require browser DLP, secure enterprise browser controls, SSE/SWG/CASB controls, MDM, workspace compliance APIs, or product-specific integrations.

## Policy

Policies are YAML files. Defaults live in `policies/default.yaml`; industry baselines live in `policies/industries/`.

```bash
promptgate init --industry finance --strict
promptgate init --industry media_entertainment --no-privacy-filter
```

Secrets default to `block`. PII and infrastructure default to `mask` or `tokenize` depending on category and profile. Raw prompt logging is disabled by default.

## Benchmark Notes

AI4Privacy PII-Masking-300k is referenced as an external benchmark option only. It is not included in this repository. Review and comply with the dataset license before using it, especially for commercial, redistributed, derivative, or training use.

The GitHub Issues Secrets Benchmark is also referenced only as an external evaluation path. PromptGate does not train on either dataset.

Run the synthetic local benchmark with:

```bash
./scripts/benchmark-local.py
```

It writes machine-readable JSON and a Markdown summary under `docs/reports/benchmarks/`.

## Release Checks

```bash
./scripts/release-check.sh
./scripts/smoke-clean-install.sh
```

Useful individual commands:

```bash
promptgate validate-policy policies/default.yaml
promptgate doctor
./scripts/test-direct-upstream.sh
./scripts/test-litellm-route.sh
./scripts/export-report.sh
./scripts/replay-audit-fixtures.sh
./scripts/assert-no-raw-leaks.sh
```

## Upstream Modes

Default mode is local mock provider:

```bash
PROMPTGATE_PROVIDER_MODE=mock
```

Explicit upstream forwarding mode:

```bash
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL=http://127.0.0.1:4000
PROMPTGATE_UPSTREAM_API_KEY=<provider-key>
```

Real provider tests require explicit credentials. PromptGate does not log upstream API keys.

LiteLLM deployment path:

```text
AI client -> PromptGate -> LiteLLM -> provider
```

Run LiteLLM as the downstream service and set `PROMPTGATE_UPSTREAM_BASE_URL` to the LiteLLM base URL. This repository documents that route but does not claim production LiteLLM routing until it is tested against the chosen deployment.
