# LiteLLM Routing Path

PromptGate's default provider mode is the local mock provider because it gives deterministic egress proof without external credentials.

Documented LiteLLM path:

```text
AI client
  -> PromptGate on 127.0.0.1
  -> scanner pipeline and policy engine
  -> rewritten request
  -> LiteLLM downstream service
  -> real provider
```

Configuration shape:

```bash
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_UPSTREAM_BASE_URL=http://127.0.0.1:4000
PROMPTGATE_UPSTREAM_API_KEY=<litellm-or-provider-key>
```

PromptGate forwards only rewritten payloads in upstream mode. Real provider or LiteLLM tests require explicit credentials and deployment-specific configuration. Do not treat this as production LiteLLM routing until the downstream LiteLLM deployment is tested.
