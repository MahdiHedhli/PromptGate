# PromptGate Live Desktop Evidence Sprint: 2026-05-02

## Status

Yellow pending owner GUI testing and real-provider MITM verification. Repo-safe automation is green so far on `feature/live-desktop-evidence`.

## What Changed

- Added OpenAI-compatible desktop app handshake endpoints:
  - `GET /v1/models`
  - `GET /models`
  - `POST /chat/completions`
- Added live desktop demo documentation for Cherry Studio.
- Added owner-only live demo values template.
- Added live prompt templates for allowed redaction/tokenization and blocked canary-secret cases.
- Added screenshot checklist for blog evidence.
- Added live-demo scripts:
  - `scripts/live-demo-preflight.sh`
  - `scripts/start-live-demo-stack.sh`
  - `scripts/stop-live-demo-stack.sh`
  - `scripts/live-demo-curl-allowed.sh`
  - `scripts/live-demo-curl-blocked.sh`
  - `scripts/assert-live-demo-no-raw-leaks.sh`
- Added tests for desktop handshake endpoints, local ignore coverage, script secret-printing safety, and live-demo leak assertion behavior.

## What Was Not Automated

- Cherry Studio GUI configuration.
- Real provider credential entry.
- Real provider MITM visual inspection.
- Screenshots for the blog.

## Owner-Only Next Steps

1. Fill `local/live-demo.env` using `docs/live-demo-values.example.md`.
2. Run `./scripts/live-demo-preflight.sh`.
3. Run `./scripts/start-live-demo-stack.sh`.
4. Configure Cherry Studio using `docs/DESKTOP_APP_DEMO.md`.
5. Send the allowed and blocked prompts from `docs/blog-assets/live-desktop-demo-prompt-template.md`.
6. Capture screenshots using `docs/blog-assets/live-demo-screenshot-checklist.md`.

## Safety Notes

- Do not commit screenshots, MITM flow files, provider credentials, Authorization headers, or raw local demo values.
- Keep browser ChatGPT and SaaS IDE claims out of the PromptGate demo evidence unless they are routed through PromptGate.
