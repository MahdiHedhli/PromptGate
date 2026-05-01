# Coverage Surface

PromptGate MVP covers API and CLI tools that can be explicitly routed through a local gateway. This is the primary path for Claude Code-style and OpenAI-compatible local testing.

Browser-based ChatGPT is not automatically intercepted. Covering browser usage requires browser DLP, secure enterprise browser controls, SSE/SWG/CASB controls, enterprise workspace controls, or compliance APIs.

IDE plugins are product-specific. Some send chat requests directly; others upload indexes or route through vendor backends outside visible chat payloads. PromptGate can only protect traffic routed through it.

MCP and tool outputs must be scanned before they become model context. PromptGate extracts nested content blocks and tool-like fields from routed requests, but host-side MCP enforcement is future work.

Agentic browser use needs two controls: model-egress scanning and browser-action controls that govern navigation, downloads, uploads, form fills, and SaaS actions.

Mac-heavy shops should combine MDM, browser/SSE controls, and a local developer gateway.

Microsoft shops may consider Purview as a future adapter, but PromptGate does not depend on it.

Non-Microsoft shops can evaluate Google Sensitive Data Protection, Nightfall-style APIs, Netskope/Zscaler-style SSE, Chrome Enterprise, and Jamf/Kandji-style MDM.

LiteLLM can sit downstream of PromptGate:

```text
AI client -> PromptGate -> LiteLLM -> provider
```

That path keeps PromptGate responsible for pre-provider scanning and leaves LiteLLM responsible for provider routing. It requires explicit downstream configuration and credentials.
