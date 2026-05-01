# Agentic Browser Threat Model

Agentic browser workflows can leak data through model prompts, tool outputs, screenshots, downloads, uploads, form fills, and SaaS side effects.

PromptGate only addresses model request egress that is routed through the local API gateway. A complete control plane also needs browser-action policy, destination allowlists, file upload controls, screenshot handling, and audit review.
