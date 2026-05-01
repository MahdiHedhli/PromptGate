# Operations

## Local Auth

PromptGate requires `PROMPTGATE_AUTH_TOKEN` by default. Generate one with:

```bash
./scripts/setup-local-key.sh
```

Unsafe unauthenticated mode exists only for local development:

```bash
PROMPTGATE_UNSAFE_DEV_NO_AUTH=true
```

Do not use unsafe mode for demos involving real tools.

## Doctor

```bash
./scripts/doctor.sh
promptgate doctor
```

Doctor checks policy validity, auth mode, provider mode, upstream config, raw prompt logging, and port availability. It redacts API keys.

## Streaming

PromptGate 0.1.0 rejects `stream=true` safely. Requests are scanned first; if they are otherwise allowed, the gateway returns a clear local error before forwarding. This prevents streaming from becoming an unscanned bypass.

## Upstream Modes

Default:

```bash
PROMPTGATE_PROVIDER_MODE=mock
```

Direct fake or real upstream, when explicitly configured:

```bash
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL=http://127.0.0.1:8791
PROMPTGATE_UPSTREAM_API_KEY=<key>
```

Real provider tests require owner-supplied credentials.

Optional MITM/proxy settings:

```bash
PROMPTGATE_UPSTREAM_HTTP_PROXY=http://127.0.0.1:8080
PROMPTGATE_UPSTREAM_CA_BUNDLE=<path to mitmproxy CA bundle>
```

These settings are disabled by default and are intended for owner-controlled verification or controlled network environments.
