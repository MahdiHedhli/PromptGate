# MITM Verification

PromptGate supports two MITM verification paths.

## Mode A: Automated Local MITM With Fake Upstream

Goal:

```text
PromptGate -> mitmproxy -> fake upstream
```

This mode does not require real provider credentials.

Run:

```bash
./scripts/test-mitm-fake-upstream.sh
```

What it does:

- Starts mitmproxy in Docker.
- Starts a local fake upstream provider in Docker.
- Starts PromptGate locally in explicit upstream mode.
- Configures `PROMPTGATE_UPSTREAM_HTTP_PROXY` to the local mitmproxy port. The automated default is `http://127.0.0.1:8898` to avoid common local port conflicts.
- Sends synthetic sensitive data through PromptGate.
- Saves local MITM captures under `local/runtime/mitm/`.
- Fails if raw synthetic values or fake keys appear in captured upstream requests.
- Passes only if placeholders such as `[PRIVATE_EMAIL_<random>]`, `[IP_ADDRESS_<random>]`, and `[CODENAME_<random>]` appear in the capture.

Manual stack controls:

```bash
./scripts/start-mitm.sh
./scripts/stop-mitm.sh
```

Do not commit files under `local/runtime/mitm/`.

## Mode B: Owner-Visible Real Provider MITM

Goal:

```text
Cherry Studio or OpenAI-compatible client -> PromptGate -> mitmproxy -> real provider
```

This mode requires owner-supplied provider credentials and optional local certificate trust setup.

### Prerequisites

- Docker or local mitmproxy.
- Provider API credentials supplied by the owner.
- PromptGate installed locally.
- A local PromptGate API key configured in `.env`.
- Synthetic test prompts only.

### Environment

Set these values in a private shell or ignored `.env` file:

```bash
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL=<provider base url>
PROMPTGATE_UPSTREAM_API_KEY=<owner supplied key>
PROVIDER_MODEL=<real upstream model id>
PROMPTGATE_UPSTREAM_HTTP_PROXY=http://127.0.0.1:8080
PROMPTGATE_UPSTREAM_CA_BUNDLE=<path to mitmproxy CA if TLS verification requires it>
```

Never paste real provider keys into docs, reports, screenshots, or GitHub issues.

### Visual Steps

1. Follow `docs/DESKTOP_APP_DEMO.md` for the Cherry Studio path.
2. Start mitmproxy or mitmweb.
3. Start PromptGate with the upstream environment above.
4. Open mitmweb, typically `http://127.0.0.1:8897` when using the live-demo helper.
5. Send the allowed live prompt through Cherry Studio or an OpenAI-compatible curl request routed through PromptGate.
6. Click the upstream provider request in mitmweb.
7. Verify the request body contains placeholders like `[PRIVATE_EMAIL_<random>]`, `[IP_ADDRESS_<random>]`, and `[CODENAME_<random>]`.
8. Verify the request body does not contain the raw demo values.
9. Repeat with `promptgate-live` and `promptgate-live-translate` if demonstrating response token translation. Both upstream requests must still contain placeholders and no raw values.
10. Send the blocked canary-secret prompt.
11. Verify no upstream provider request is created for the blocked prompt.

### Safety Notes

- Do not use real customer data.
- Do not use real secrets as prompt content.
- Do not commit mitmproxy flow files.
- Do not screenshot provider API keys, Authorization headers, or raw payloads.
- Stop mitmproxy and remove local captured flows after testing if desired.

### Troubleshooting

- TLS certificate trust problems: with `./scripts/start-live-demo-stack.sh`, the Docker mitmproxy CA is mounted under ignored `local/runtime/live-demo/mitmproxy/` and `PROMPTGATE_UPSTREAM_CA_BUNDLE` is set automatically unless already configured. For manual mitmproxy runs, use mitmproxy's generated CA and set `PROMPTGATE_UPSTREAM_CA_BUNDLE`.
- Provider 401: verify the owner-supplied provider key in the local shell only.
- HTTP proxy not used: confirm `PROMPTGATE_UPSTREAM_HTTP_PROXY` is set in the environment that launches PromptGate.
- mitmweb shows only local client traffic: ensure PromptGate is in `upstream` mode and the upstream HTTP proxy env var is set.
- Docker networking on macOS: for fake-upstream mode, use the provided scripts. For real-provider mode, keep PromptGate and mitmproxy on host-reachable ports.
