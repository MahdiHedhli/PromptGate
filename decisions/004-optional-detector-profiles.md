# 004: Optional Detector Profiles

Status: Accepted

PromptGate's default install must stay offline and lightweight. Regex, secrets, custom keyword rules, sample DLP imports, and normalization remain default-local.

Privacy Filter and Presidio-style detectors are optional profiles. PromptGate includes a mockable Privacy Filter interface and a local-service configuration shape, but the default install does not download model weights or require a separate detector service.

If a policy enables a required local detector service and the service is unavailable, PromptGate should fail closed with a clear operator error. CI uses mocks and synthetic data only.
