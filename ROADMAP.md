# PromptGate 14-Day Roadmap

## Day 1

- Build local FastAPI gateway and mock provider.
- Implement YAML policy, scanners, token vault, redaction, and egress tests.
- Publish coverage limitations and benchmark notes.

## Days 2-4

- Added fail-closed policy validation and schema hardening.
- Expanded extractor coverage for OpenAI, Anthropic, Responses-style, tool, MCP, metadata, and JSON-string argument shapes.
- Added safer mapped normalization and conservative block behavior for uncertain mappings.
- Added auth-required defaults, explicit upstream forwarding config, synthetic latency benchmarks, and LiteLLM routing docs.

## Days 5-7

- Add LiteLLM routing option and real-provider smoke path behind explicit credentials.
- Add report export and replayable audit fixtures.

## Days 8-10

- Harden Docker quickstart, auth, and operational docs.
- Add browser and IDE coverage diagrams as future paths.

## Days 11-14

- Polish demo, blog evidence, and MVP release checklist.
- Add response token translation demo toggle so `promptgate-live` shows placeholders and `promptgate-live-translate` restores known scoped tokens locally while MITM upstream traffic remains tokenized.
