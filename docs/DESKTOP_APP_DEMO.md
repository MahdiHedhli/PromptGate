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
- Model ID: `promptgate-live` or another model listed by `http://127.0.0.1:8787/v1/models`

For real upstream demos, set `PROVIDER_MODEL` or `PROMPTGATE_UPSTREAM_MODEL` in `local/live-demo.env` to a real provider model such as `gpt-4o-mini`. PromptGate can expose friendly desktop model IDs like `promptgate-live` and rewrite them to the real provider model only after scanning.

Cherry Studio sends OpenAI-compatible requests with `stream=true` during normal chat and provider checks. PromptGate scans, blocks, masks, or tokenizes the request before opening the upstream stream. The MVP does not restore tokens in streamed provider responses.

Fallbacks if Cherry Studio cannot route through PromptGate:

- AnythingLLM Desktop
- Jan
- LM Studio client mode, if custom OpenAI-compatible upstream is available

Do not switch apps silently. Record the reason in the demo notes.

## 6. Run Curl Sanity Checks

Before GUI screenshots:

```bash
./scripts/live-demo-curl-allowed.sh
./scripts/assert-live-demo-no-raw-leaks.sh
./scripts/live-demo-curl-blocked.sh
```

The allowed script verifies provider reachability through PromptGate. The blocked script verifies the canary secret is blocked before upstream egress.

## 7. Run Desktop GUI Prompts

Use `docs/blog-assets/live-desktop-demo-prompt-template.md`.

1. Send the allowed redaction/tokenization prompt.
2. Screenshot the desktop app input.
3. Screenshot the desktop app response.
4. Open mitmweb.
5. Screenshot the upstream provider request body showing placeholders only.
6. Confirm raw demo email, IP, internal domain, and codename are absent upstream.
7. Send the blocked-secret prompt.
8. Screenshot the desktop app block/error response.
9. Confirm no upstream provider request was created for the blocked prompt.

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
