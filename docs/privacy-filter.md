# Privacy Filter Integration

PromptGate treats OpenAI Privacy Filter-style detection as optional and first-class. The scanner interface accepts a provider that emits labels and spans; policy decides whether each finding is blocked, masked, tokenized, allowed, or audited.

Current MVP status:

- `promptgate.scan.privacy_filter` defines the provider protocol.
- Tests use a mock provider.
- A local-service provider shape is implemented and tested with mocked HTTP.
- The repo works without downloading a model.

Label mapping:

| Privacy label | PromptGate category |
|---|---|
| private_person | private_person |
| private_address | private_address |
| private_email | private_email |
| private_phone | private_phone |
| private_url | private_url |
| private_date | private_date |
| account_number | account_number |
| secret | secret |

Local-service policy shape:

```yaml
detectors:
  privacy_filter:
    enabled: true
    mode: local_service
    url: http://privacy-filter:8081
    timeout_seconds: 2
    fail_closed: true
```

Expected local service API:

```http
POST /scan
Content-Type: application/json

{"text":"Email alice@example.com"}
```

Response:

```json
{"findings":[{"label":"private_email","start":6,"end":23,"score":0.99}]}
```

Real integration path: run a local Privacy Filter service that implements the API above, enable the local-service policy shape, and keep raw prompt logging disabled. The default install does not download model weights. Model size, cold start time, hardware needs, and label quality must be validated by the owner before any public claim of real model-backed coverage.
