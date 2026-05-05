# Desktop App Demo

This guide prepares the owner-visible live proof:

```text
Cherry Studio -> PromptGate -> mitmproxy/mitmweb -> real upstream provider
```

The owner supplies provider credentials locally. Do not commit credentials, screenshots, MITM flows, or demo values.

## 1. Checkout And Restart

```bash
git checkout feature/live-desktop-evidence
git pull --ff-only
./scripts/install-demo-deps.sh
./scripts/stop-live-demo-stack.sh || true
```

If another PromptGate process is on `127.0.0.1:8787`, stop it before starting the live stack. This avoids testing old code.

To install project-local dependencies without installing GUI apps:

```bash
./scripts/install-demo-deps.sh --install
```

Optional GUI/tool installs, if missing:

```bash
brew install --cask cherry-studio
brew install mitmproxy
```

Docker is preferred for the MITM helper, so local mitmproxy is optional.

## 2. Create Local Demo Values

Create ignored local files:

```bash
cp .env.example .env
./scripts/setup-local-key.sh
mkdir -p local
$EDITOR local/live-demo.env
```

Use `docs/live-demo-values.example.md` as the template. Keep provider credentials and owner demo values only in ignored local files.

## 3. Preflight

```bash
./scripts/live-demo-preflight.sh
```

Warnings about missing provider credentials are expected until the owner fills `local/live-demo.env`.

## 4. Start MITM And PromptGate

For local mock-provider Cherry Studio testing without real provider credentials, run PromptGate in the foreground:

```bash
./scripts/run-promptgate-local.sh
```

Leave that terminal open while Cherry Studio is connected to `http://127.0.0.1:8787/v1`.

For the owner-visible real-provider MITM demo, use:

```bash
./scripts/start-live-demo-stack.sh
```

The script starts:

- PromptGate on `http://127.0.0.1:8787`
- OpenAI-compatible app base URL at `http://127.0.0.1:8787/v1`
- mitmweb on `http://127.0.0.1:8897`
- mitmweb password `promptgate-local` by default, or `PROMPTGATE_LIVE_MITMWEB_PASSWORD` if overridden
- MITM capture files under ignored `local/runtime/live-demo/`
- mitmproxy CA material under ignored `local/runtime/live-demo/mitmproxy/`

For the Docker MITM path, the script mounts mitmproxy CA material locally and automatically sets `PROMPTGATE_UPSTREAM_CA_BUNDLE` for PromptGate unless you already set one in `local/live-demo.env`.

## 5. Configure Cherry Studio

In Cherry Studio, add a custom provider:

- Provider name: `PromptGate Local`
- Provider type: `OpenAI`
- API address/Base URL: `http://127.0.0.1:8787/v1`
- API key: the local PromptGate auth token from `.env`, not the provider key
- Model ID: `promptgate-live` for translation OFF or `promptgate-live-translate` for translation ON

For real upstream demos, set `PROVIDER_MODEL` or `PROMPTGATE_UPSTREAM_MODEL` in `local/live-demo.env` to a real provider model such as `gpt-4o-mini`. PromptGate can expose friendly desktop model IDs like `promptgate-live` and rewrite them to the real provider model only after scanning.

Cherry Studio sends OpenAI-compatible requests with `stream=true` during normal chat and provider checks. PromptGate scans, blocks, masks, or tokenizes the request before opening the upstream stream. Response token translation is optional: `promptgate-live` returns placeholders to the desktop app, while `promptgate-live-translate` translates known scoped response tokens back to local controlled values after the provider response is received.

Fallbacks if Cherry Studio cannot route through PromptGate:

- AnythingLLM Desktop
- Jan
- LM Studio client mode, if custom OpenAI-compatible upstream is available

Do not switch apps silently. Record the reason in the demo notes.

## 6. Run Curl Sanity Checks

Before GUI screenshots:

```bash
./scripts/live-demo-curl-allowed.sh --translate off
./scripts/live-demo-curl-allowed.sh --translate on
./scripts/assert-live-demo-translation.sh
./scripts/assert-live-demo-no-raw-leaks.sh
./scripts/live-demo-curl-blocked.sh
```

The allowed script verifies provider reachability through PromptGate in both translation modes. The translation assertion checks that the OFF response contains placeholders, the ON response restores local controlled values, and MITM upstream captures remain tokenized. The blocked script verifies the canary secret is blocked before upstream egress.

## 7. Run Desktop GUI Prompts

Use `docs/blog-assets/live-desktop-demo-prompt-template.md`.

1. Select `promptgate-live` and send the allowed prompt.
2. Screenshot the response showing placeholders.
3. Open mitmweb and screenshot the upstream request body showing placeholders only.
4. Select `promptgate-live-translate` and send the same allowed prompt.
5. Screenshot the response showing restored local controlled values.
6. Open mitmweb and screenshot the upstream request body still showing placeholders only.
7. Confirm raw demo email, IP, internal domain, and codename are absent upstream in both modes.
8. Send the blocked-secret prompt.
9. Screenshot the desktop app block/error response.
10. Confirm no upstream provider request was created for the blocked prompt.

## 8. Safety

- Use synthetic or owner-controlled demo values only.
- Hide or crop Authorization headers.
- Hide provider API keys and account IDs.
- Do not publish mitmproxy flow files.
- Do not publish raw `local/live-demo.env`.
- Do not use browser ChatGPT screenshots as PromptGate coverage evidence.

## 9. Stop

```bash
./scripts/stop-live-demo-stack.sh
```

Use `./scripts/stop-live-demo-stack.sh --delete-evidence` only when you intentionally want to delete local runtime evidence.
