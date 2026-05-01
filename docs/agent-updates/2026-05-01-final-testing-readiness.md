# PromptGate Final Testing Readiness: 2026-05-01

## One-line Status

Green: automated local correctness, fake upstream routing, fake LiteLLM route shape, benchmark generation, report export, replay fixtures, leak assertions, and MITM fake-upstream verification are passing.

## What Changed

- Added optional upstream proxy and CA bundle support through environment configuration.
- Added Docker-based MITM fake-upstream verification.
- Added owner-facing MITM verification docs for fake and real-provider paths.
- Expanded tests for policy failure modes, unsafe dev auth behavior, system/developer payload extraction, normalization span mapping, and MITM/proxy forwarding configuration.
- Updated human testing docs with a staged sequence and clear owner-only boundary.
- Added safe blog evidence notes and MITM screenshot guidance.
- Added MITM verification to the release-check gate.

## Commands Run

| Command | Result |
|---|---:|
| `.venv/bin/python -m pytest -q` | pass, 39 tests |
| `./scripts/release-check.sh` | pass |
| `./scripts/smoke-clean-install.sh` | pass |
| `./scripts/test-egress.sh` | pass |
| `./scripts/test-direct-upstream.sh` | pass |
| `./scripts/test-litellm-route.sh` | pass |
| `./scripts/test-mitm-fake-upstream.sh` | pass |
| `./scripts/benchmark-local.py` | pass |
| `./scripts/export-report.sh` | pass |
| `./scripts/replay-audit-fixtures.sh` | pass |
| `./scripts/assert-no-raw-leaks.sh` | pass |
| `.venv/bin/promptgate validate-policy policies/default.yaml` | pass |
| `docker compose up -d --build` and health check | pass |

## Automated Coverage Added

- HTTP proxy and CA bundle config propagation for upstream mode.
- Fake MITM route: PromptGate to mitmproxy to fake provider.
- Streaming remains intentionally rejected before upstream forwarding.
- Additional normalization mapping tests for safe and uncertain spans.
- Additional auth tests for explicit unsafe dev mode.

## Owner-only Work Remaining

- Real provider MITM verification with owner-supplied credentials.
- Real Claude Code routing verification on the owner's machine.
- Any public release or package publishing decision.

## MITM Verification Summary

Read `docs/MITM_VERIFICATION.md`.

Automated fake path:

```text
PromptGate -> mitmproxy -> fake upstream
```

Owner-visible real-provider path:

```text
Claude Code or OpenAI-compatible client -> PromptGate -> mitmproxy -> real provider
```

Use synthetic data only. Do not publish API keys, Authorization headers, real provider payloads, or mitmproxy flow files.

## Risks And Limitations

- Real-provider MITM requires owner credentials and local TLS/proxy setup.
- Production LiteLLM behavior still needs validation against the owner's deployment.
- Streaming is not supported in 0.1.0; it is rejected safely.
- Browser ChatGPT and SaaS IDE backends are outside the local API gateway scope.

## GitHub

- Repository: `https://github.com/MahdiHedhli/PromptGate`
- Visibility: private
- Branch: `main`
- Commit: `6c3f42aeff2e317af8dd2d3f9ae343877ba33e98`
