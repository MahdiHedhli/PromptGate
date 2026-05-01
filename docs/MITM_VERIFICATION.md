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
- Passes only if placeholders such as `[PRIVATE_EMAIL_001]`, `[IP_ADDRESS_001]`, and `[CODENAME_001]` appear in the capture.

Manual stack controls:

```bash
./scripts/start-mitm.sh
./scripts/stop-mitm.sh
```

Do not commit files under `local/runtime/mitm/`.

## Mode B: Owner-Visible Real Provider MITM

Goal:

```text
Claude Code or OpenAI-compatible client -> PromptGate -> mitmproxy -> real provider
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
PROMPTGATE_UPSTREAM_HTTP_PROXY=http://127.0.0.1:8080
PROMPTGATE_UPSTREAM_CA_BUNDLE=<path to mitmproxy CA if TLS verification requires it>
```

Never paste real provider keys into docs, reports, screenshots, or GitHub issues.

### Visual Steps

1. Start mitmproxy or mitmweb.
2. Start PromptGate with the upstream environment above.
3. Open mitmweb, typically `http://127.0.0.1:8081`.
4. Send a synthetic prompt through Claude Code or an OpenAI-compatible curl request routed through PromptGate.
5. Click the upstream provider request in mitmweb.
6. Verify the request body contains placeholders like `[PRIVATE_EMAIL_001]`, `[IP_ADDRESS_001]`, and `[CODENAME_001]`.
7. Verify the request body does not contain the raw synthetic values.
8. Send a synthetic blocked-secret prompt.
9. Verify no upstream provider request is created for the blocked prompt.

### Safety Notes

- Do not use real customer data.
- Do not use real secrets as prompt content.
- Do not commit mitmproxy flow files.
- Do not screenshot provider API keys, Authorization headers, or raw payloads.
- Stop mitmproxy and remove local captured flows after testing if desired.

### Troubleshooting

- TLS certificate trust problems: use mitmproxy's generated CA and set `PROMPTGATE_UPSTREAM_CA_BUNDLE` if the provider client requires a custom CA bundle.
- Provider 401: verify the owner-supplied provider key in the local shell only.
- HTTP proxy not used: confirm `PROMPTGATE_UPSTREAM_HTTP_PROXY` is set in the environment that launches PromptGate.
- mitmweb shows only local client traffic: ensure PromptGate is in `upstream` mode and the upstream HTTP proxy env var is set.
- Docker networking on macOS: for fake-upstream mode, use the provided scripts. For real-provider mode, keep PromptGate and mitmproxy on host-reachable ports.
