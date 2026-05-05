# Live Desktop Demo Prompt Template

Use these prompts in Cherry Studio or the selected desktop LLM app after configuring it to route through PromptGate.

## Allowed Redaction/Tokenization Prompt

```text
I am testing a local AI DLP gateway called PromptGate.

Use the exact values I provide below when summarizing. Do not invent replacements.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Task:
1. Summarize the finding in two sentences.
2. Include the server IP, internal domain, project codename, and owner email exactly as shown in your input.

Controlled demo values:
- Owner email: ${DEMO_EMAIL}
- Internal domain: ${DEMO_INTERNAL_DOMAIN}
- Server IP: ${DEMO_INTERNAL_IP}
- Project codename: ${DEMO_CODENAME}
```

Expected outcome:

- With `promptgate-live`, the desktop response contains placeholders.
- With `promptgate-live-translate`, the desktop response restores the local controlled values.
- In both modes, MITM upstream request body contains placeholders for the email, domain, IP, and codename.
- In both modes, MITM upstream request body does not contain the raw demo values.

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
