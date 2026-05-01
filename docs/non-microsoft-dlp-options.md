# Non-Microsoft DLP Options

PromptGate's adapter boundary is intentionally vendor-neutral. Future runtime adapters could call Google Sensitive Data Protection, Nightfall-style APIs, custom internal DLP services, or SSE products such as Netskope and Zscaler.

The MVP includes `local_yaml`, `sample_import`, and a webhook stub. It does not include production vendor adapters.
