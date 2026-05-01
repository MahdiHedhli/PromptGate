# 005: Coverage Boundaries

Status: Accepted

PromptGate protects API and CLI traffic that is explicitly routed through it. It does not automatically intercept browser ChatGPT, Claude.ai, SaaS IDE backends, vendor-managed code indexes, direct file uploads, or browser action planes.

Those surfaces require separate controls: browser DLP, enterprise browser policy, SSE or SWG enforcement, MDM, IDE-specific controls, SaaS admin settings, MCP/tool output scanning, and agent action controls.

PromptGate docs must keep this boundary visible so the MVP is credible and users do not infer coverage that is not implemented.
