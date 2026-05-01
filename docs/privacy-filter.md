# Privacy Filter Integration

PromptGate treats OpenAI Privacy Filter-style detection as optional and first-class. The scanner interface accepts a provider that emits labels and spans; policy decides whether each finding is blocked, masked, tokenized, allowed, or audited.

Current MVP status:

- `promptgate.scan.privacy_filter` defines the provider protocol.
- Tests use a mock provider.
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

Real integration path: implement `PrivacyFilterProvider.find(text)` with the model runtime, enable `detectors.privacy_filter: enabled`, and keep raw prompt logging disabled.
