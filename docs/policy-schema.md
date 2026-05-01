# PromptGate Policy Schema

PromptGate policies are editable YAML files. The loader fails closed when required sections are missing, detector names are unknown, actions are invalid, rule IDs duplicate, severity values are invalid, or custom regex rules do not compile.

Required top-level sections:

```yaml
profile: security_consulting
mode: enforce
logging: {}
detectors: {}
actions: {}
tokenization: {}
allowlist: []
rules: []
```

Supported profiles:

- `security_consulting`
- `software_saas`
- `finance`
- `healthcare`
- `legal`
- `media_entertainment`

Supported modes:

- `enforce`: block/mask/tokenize according to policy.
- `audit`: record redacted finding metadata and allow.
- `dry-run`: same behavior as audit for MVP testing.

Supported actions:

- `block`: reject the request locally.
- `mask`: replace the original span with `[CATEGORY_REDACTED]`.
- `tokenize`: replace with scoped random placeholders by default, such as `[PRIVATE_EMAIL_a3f9c1d2e4b56789]`.
- `allow`: send unchanged.
- `audit`: record redacted metadata and allow unchanged.

Supported detectors:

- `regex`
- `secrets`
- `privacy_filter`
- `normalization`
- `sample_dlp_imports`

Privacy Filter values are `optional`, `enabled`, `disabled`, `true`, `false`, or a local-service configuration:

```yaml
detectors:
  privacy_filter:
    enabled: true
    mode: local_service
    url: http://privacy-filter:8081
```

The MVP ships with a mockable provider interface and does not download model files by default.

Tokenization defaults:

```yaml
tokenization:
  mode: scoped_random
  ttl_seconds: 3600
  max_conversations: 100
  restore_responses: false
```

`deterministic` mode remains available for demos and reproducible tests, but it is opt-in because sequential tokens are easier to guess than scoped random tokens.

Rules:

```yaml
rules:
  - id: client_codename
    type: keyword
    values: ["Project Raven"]
    category: client_codename
    action: tokenize
    token_prefix: CODENAME
    severity: high
    audit_only: true

  - id: internal_ticket
    type: regex
    pattern: "\\b[A-Z]{2,10}-SEC-[0-9]{3,8}\\b"
    category: internal_ticket
    action: tokenize
    token_prefix: TICKET
    severity: medium
```

Profiles are baseline safeguards, not compliance guarantees. They do not replace enterprise DLP, legal review, data inventory, MDM, browser controls, SSE/SWG/CASB, or vendor-specific governance.
