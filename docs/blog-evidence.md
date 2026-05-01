# Blog Evidence Notes

## Architecture

```text
AI client -> PromptGate -> extractor -> scanners -> policy -> redactor/token vault -> provider mode
Provider modes: mock, direct upstream, LiteLLM route shape, MITM fake upstream.
```

## Test Evidence Chain

1. `pytest` verifies policy validation, auth, extraction, rewriting, normalization, and streaming rejection.
2. `test-egress.sh` proves the mock provider receives placeholders and blocked secrets do not forward.
3. `test-direct-upstream.sh` proves direct upstream mode receives rewritten payloads only.
4. `test-litellm-route.sh` proves the local LiteLLM/provider route shape with rewritten payloads only.
5. `test-mitm-fake-upstream.sh` proves traffic routed through mitmproxy contains placeholders and not raw synthetic values.
6. `assert-no-raw-leaks.sh` checks generated runtime reports for raw synthetic sensitive values.

## Expected Redacted Upstream Body

```json
{
  "model": "mock",
  "messages": [
    {
      "role": "user",
      "content": "Email [PRIVATE_EMAIL_a3f9c1d2e4b56789] from [IP_ADDRESS_4b8e1a92cd3f7e60] about [CODENAME_9a81fb320a5c4d77]."
    }
  ]
}
```

## MITM Screenshot Checklist

- mitmweb request list showing an upstream request.
- Request body showing placeholders.
- No Authorization header visible unless redacted.
- No raw synthetic sensitive values in request body.
- Terminal showing blocked secret request returns a local PromptGate error.

## What Not To Screenshot Or Publish

- Real provider API keys.
- Authorization headers.
- Real customer data.
- Raw provider payloads containing real data.
- mitmproxy flow files.
- Local `.env` files.
- Local research notes or handoff prompts.

## Honest Limitations

- Browser ChatGPT is not intercepted by this local API gateway.
- SaaS IDE backends and vendor-managed code indexes are not automatically covered.
- Streaming is rejected safely in 0.1.0 rather than proxied.
- Real Privacy Filter model integration remains optional and mockable.
- Production LiteLLM routing should be tested against the owner's deployment before public claims.
