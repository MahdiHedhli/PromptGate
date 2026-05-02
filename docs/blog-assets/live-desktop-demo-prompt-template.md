# Live Desktop Demo Prompt Template

Use these prompts in Cherry Studio or the selected desktop LLM app after configuring it to route through PromptGate.

## Allowed Redaction/Tokenization Prompt

```text
I'm reviewing this PromptGate policy and threat model excerpt before publishing the MVP.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Please summarize the risk and suggest what to test next.

Operational details from my local demo environment:
- Contact: ${DEMO_EMAIL}
- Internal service: ${DEMO_INTERNAL_DOMAIN}
- Internal IP: ${DEMO_INTERNAL_IP}
- Project codename: ${DEMO_CODENAME}
```

Expected outcome:

- Desktop app receives a normal model response.
- MITM upstream request body contains placeholders for the email, domain, IP, and codename.
- MITM upstream request body does not contain the raw demo values.

## Blocked Secret Prompt

```text
I'm reviewing this PromptGate policy and threat model excerpt before publishing the MVP.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Please summarize the risk and suggest what to test next.

Do not process this fake canary secret: ${DEMO_CANARY_SECRET}
```

Expected outcome:

- Desktop app shows a local PromptGate block/error response.
- MITM shows no new upstream provider request for the blocked prompt.
