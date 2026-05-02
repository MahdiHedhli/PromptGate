# PromptGate Release Readiness

| Gate | Status | Evidence command | Artifact path | Remaining owner action |
|---|---|---|---|---|
| Local Python quickstart | Green | `./scripts/smoke-clean-install.sh` | terminal output | Run on owner machine |
| Docker quickstart | Green | `docker compose up -d --build && curl /health` | Docker container | Run on owner machine |
| Auth defaults | Green | pytest auth tests, `./scripts/doctor.sh` | tests/test_auth_and_upstream.py | Choose demo token handling |
| Policy validation | Green | `promptgate validate-policy policies/default.yaml` | policies/default.yaml | Edit profile as needed |
| Scoped tokenization | Green | pytest token vault tests | tests/test_redaction.py | Decide if demos need deterministic mode |
| Audit-only rollout | Green | pytest audit-only tests | tests/test_redaction.py | Decide rollout policy for new org rules |
| Egress proof | Green | `./scripts/test-egress.sh` | mock provider capture | Run before demo |
| Direct upstream routing | Green | `./scripts/test-direct-upstream.sh` | docs/reports/generated/fake-upstream-capture.json | Real provider credentials optional |
| LiteLLM route shape | Green | `./scripts/test-litellm-route.sh` | fake upstream capture | Production LiteLLM deployment not claimed |
| Desktop app handshake | Green | pytest `/v1/models`, `/models`, `/chat/completions` tests | tests/test_auth_and_upstream.py | Owner configures Cherry Studio GUI |
| Live desktop demo tooling | Green | pytest live-demo script tests | scripts/live-demo-*.sh | Owner supplies local credentials and demo values |
| Streaming behavior | Green | pytest streaming rejection test | tests/test_gateway_egress.py | Decide when to add streaming support |
| MITM fake-upstream verification | Green | `./scripts/test-mitm-fake-upstream.sh` | local/runtime/mitm/ ignored captures | Owner can run visual MITM next |
| Real-provider MITM | Yellow | docs/MITM_VERIFICATION.md | owner local mitmproxy | Requires owner credentials |
| Benchmarks | Green | `./scripts/benchmark-local.py` | docs/reports/benchmarks/latest.md | Treat as synthetic local evidence |
| Report export | Green | `./scripts/export-report.sh` | docs/reports/generated/promptgate-report.md | Review before blog use |
| Leak assertions | Green | `./scripts/assert-no-raw-leaks.sh` | runtime reports | Expand needles for new fixtures |
| Replayable audit fixtures | Green | `./scripts/replay-audit-fixtures.sh` | tests/fixtures/replay | Add more fixtures over time |
| CI workflow | Green | `.github/workflows/test.yml` | GitHub Actions config | Runs after repo publish |
| Repo hygiene | Green | `.gitignore`, `.dockerignore`, `git status --short` | root config files | Review before first commit |
| Docs and limitations | Green | docs coverage files | docs/ | Owner editorial review |
| External dataset licensing | Green | docs/benchmark-notes.md | docs/benchmark-notes.md | License review before external use |
| Privacy Filter integration | Yellow | mocked and local-service interface tests | docs/privacy-filter.md | Real model runtime is owner-only |
| Browser and IDE scope limits | Green | docs/coverage-surface.md | docs/coverage-surface.md | Keep public claims narrow |
| Open owner decisions | Yellow | this file | N/A | Repo publishing, branding, real-provider smoke |
