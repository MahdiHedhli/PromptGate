# PromptGate Threat Model

PromptGate is a local-first DLP gateway for AI prompts, tools, and model context. It inspects API and CLI model requests before provider egress and blocks, masks, tokenizes, allows, or audits findings according to policy.

## Assets

- Prompt text, system and developer messages, tool outputs, MCP-like tool results, nested JSON-string arguments, metadata text, file-like text blocks, and provider-specific request fields.
- Secrets, API keys, private keys, database URLs, internal domains, IP addresses, codenames, and private personal data.
- Policy files and imported local DLP samples.
- Token vault mappings.
- Audit events, benchmark outputs, MITM captures, logs, and generated reports.
- Optional detector-service traffic.

## Trust Boundaries

```text
AI client -> PromptGate local gateway -> detector pipeline -> policy/action engine
PromptGate -> optional local detector service
PromptGate -> optional LiteLLM downstream route
PromptGate -> upstream model provider
PromptGate -> local logs, reports, and benchmark artifacts
```

Loopback client-to-PromptGate traffic is trusted only as local operator traffic and still requires a local API key by default. Anything crossing from PromptGate to LiteLLM, a provider, telemetry, or a detector service is treated as sensitive egress.

## Defends Against

- Accidental prompt leakage by cooperative users.
- Client, NDA, project, and internal codename disclosure.
- Secret leakage through prompts, tool outputs, metadata, or nested arguments.
- Infrastructure disclosure such as internal domains and IP addresses.
- Basic obfuscated sensitive text, including separator-heavy values, leetspeak, zero-width characters, and normalized email patterns.
- Streaming bypass in the MVP by rejecting `stream=true` safely before upstream forwarding.

## Does Not Defend Against

- Malicious insiders or users intentionally bypassing the gateway.
- Browser ChatGPT, Claude.ai, or other SaaS browser chat unless traffic is separately controlled.
- SaaS IDE backends or vendor-managed code indexes that do not route through PromptGate.
- Local host compromise, malware, root access, screenshots, clipboard exfiltration, or direct file transfer.
- Provider behavior after a rewritten payload is received.
- Unrestricted image and file uploads.
- Agentic browser actions or tool actions outside the model-request boundary.

## Token-Map Ledger Risk

Tokenization preserves workflow context but creates a sensitive in-memory ledger. PromptGate defaults to scoped random tokenization with TTL and LRU eviction, no disk persistence, and no raw mapping in status, logs, reports, or audit events. Deterministic sequential tokens are opt-in for demos and reproducible tests.

## Prompt-Injection Risk Against Restoration

PromptGate does not restore response tokens by default. Unknown tokens are never restored, and scoped tokens from conversation A do not restore in conversation B. If response restoration is added later, it must preserve these properties and treat LLM-emitted tokens as untrusted text.

## Coverage Boundary

Browser, IDE, MCP, and agentic browser surfaces require separate controls. PromptGate scans MCP/tool output when it becomes model context in routed API traffic, but it does not control the tool action plane itself.
