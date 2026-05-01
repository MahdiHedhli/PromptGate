# Industry Profiles

PromptGate profiles are starter policies for local developer traffic. They are not compliance certifications.

## Security Consulting And Pentest

Protects client codenames, internal tickets, internal domains, infrastructure indicators, file paths, secrets, and API keys. Good default for security assessment work where prompts may include logs, tool output, hostnames, or client identifiers.

## Software SaaS

Protects tenant IDs, customer contact data, internal domains, service URLs, database URLs, API keys, and local file paths. Good default for product engineering and support workflows.

## Finance

Strict defaults for account-like identifiers, contact data, infrastructure, and secrets. This profile blocks account-number categories by default.

## Healthcare

Strict defaults for contact data, person/date-like Privacy Filter findings, medical-record-like identifiers, and secrets. This profile is a safeguard baseline only and is not a HIPAA compliance claim.

## Legal

Protects matter numbers, person/contact-like data, client identifiers, and secrets. It is intended for local prompt hygiene, not privilege determination.

## Media And Entertainment

Protects unreleased project codenames, contacts, private URLs, internal domains, and secrets.

## General Enterprise

Use `software_saas` or `security_consulting` as the closest current baseline, then edit custom rules and sample imports.
