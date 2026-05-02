# Live Demo Screenshot Checklist

Capture only owner-controlled demo values and redacted provider traffic.

## Capture

- Desktop app provider settings showing `http://127.0.0.1:8787/v1` as the API address, with API key hidden.
- Desktop app allowed prompt input.
- Desktop app allowed prompt response.
- mitmweb upstream request body showing placeholders only.
- Terminal output from `scripts/assert-live-demo-no-raw-leaks.sh`.
- Blocked-secret prompt error in the desktop app.
- mitmweb request list showing no new upstream request for the blocked prompt.

## Do Not Capture

- Authorization headers.
- Provider API keys.
- Provider account IDs.
- Real customer data.
- Raw `local/live-demo.env`.
- mitmproxy flow files.
- Unrelated browser tabs or private desktop content.

## Blog Caption Guidance

Use language like: "PromptGate routed a real desktop LLM app through a local DLP gateway. MITM verification shows the provider request contained placeholders instead of raw demo values. The blocked canary secret created no upstream request."
