# PromptGate Human Testing

Run these from `/Users/mhedhli/Documents/Coding/PromptGate`.

Owner involvement begins at the real-provider and Claude Code tests. Everything before that is automated and uses local fake services.

## 1. Python Local Demo

```bash
python3.12 -m venv .venv || python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
./scripts/setup-local-key.sh
./scripts/init-policy.sh security_consulting
set -a; source .env; set +a
.venv/bin/python -m uvicorn promptgate.server:app --host 127.0.0.1 --port 8787
```

In another terminal:

```bash
./scripts/test-egress.sh
```

## 2. Docker Local Demo

```bash
cp .env.example .env
./scripts/setup-local-key.sh
./scripts/init-policy.sh security_consulting
docker compose up -d --build
curl -fsS http://127.0.0.1:8787/health
./scripts/test-egress.sh
```

## 3. Claude Code Routing Check

```bash
./scripts/setup-claude-code.sh
```

Use the printed environment variables in a shell where Claude Code can route Anthropic-compatible requests to PromptGate.

## 4. OpenAI-Compatible Curl Check

```bash
./scripts/setup-openai-compatible.sh
```

Then run the printed curl command or use `OPENAI_BASE_URL=http://127.0.0.1:8787/v1` and `OPENAI_API_KEY` set to the local PromptGate token.

## 5. Direct Fake Upstream

```bash
./scripts/test-direct-upstream.sh
```

Expected result: fake upstream capture contains placeholders and redacted headers only.

## 6. Fake LiteLLM Route Shape

```bash
./scripts/test-litellm-route.sh
```

This uses a local fake LiteLLM/provider-compatible upstream. It proves the route shape without external credentials.

## 7. Local MITM Fake-Upstream Verification

```bash
./scripts/test-mitm-fake-upstream.sh
```

Expected result: mitmproxy capture under `local/runtime/mitm/` contains placeholders and no raw synthetic sensitive values.

## 8. Streaming Behavior

Recommended:

```bash
./scripts/test-streaming-rejection.sh
```

Manual equivalent:

```bash
set -a
source .env
set +a

curl -s http://127.0.0.1:8787/v1/chat/completions \
  -H "Authorization: Bearer $PROMPTGATE_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","stream":true,"messages":[{"role":"user","content":"hello"}]}'
```

Expected result: local 400 response explaining that streaming is rejected safely in 0.1.0.

## 9. Release Gates

```bash
./scripts/release-check.sh
./scripts/smoke-clean-install.sh
```

## 10. Reports And Benchmarks

```bash
./scripts/benchmark-local.py
./scripts/export-report.sh
./scripts/replay-audit-fixtures.sh
./scripts/assert-no-raw-leaks.sh
```

Inspect:

- `docs/reports/benchmarks/latest.md`
- `docs/reports/generated/promptgate-report.md`
- `docs/reports/generated/fake-upstream-capture.json`

## 11. Real Provider MITM Verification

Read [MITM_VERIFICATION.md](MITM_VERIFICATION.md). This requires owner-supplied provider credentials.

High-level flow:

```text
OpenAI-compatible client or Claude Code -> PromptGate -> mitmproxy -> real provider
```

Use synthetic prompt content only. Do not screenshot API keys, Authorization headers, or raw real provider payloads.

## 12. Claude Code Routing Test

```bash
./scripts/setup-claude-code.sh
```

Use the printed local environment variables in the shell where Claude Code is launched. Owner credentials and account-specific Claude Code setup are owner-only.

## 13. Clean Up Local Runtime Artifacts

```bash
./scripts/stop-mitm.sh || true
rm -rf local/runtime/mitm/*
```

Do not commit local runtime artifacts.

## 14. Blog Screenshot Checklist

- Terminal showing `release-check` passing.
- Mock provider egress proof output.
- Redacted report table.
- Benchmark summary table.
- `curl /status` showing detector state without secrets.
- Mermaid architecture diagram in `docs/blog-assets/architecture.md`.
- MITM request body with placeholders and no raw synthetic values.

## Optional Owner-Credential Tests

- Real provider smoke test through explicit upstream mode.
- Real Claude Code interaction routed through PromptGate.
- Cursor or IDE experiment only if the tool can route model traffic through PromptGate.
- Real Privacy Filter integration if a model runtime is installed.
