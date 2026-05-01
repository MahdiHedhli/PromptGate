# Benchmarks

PromptGate benchmark evidence uses synthetic local data only. The repo does not download, vendor, train on, or redistribute AI4Privacy PII-Masking-300k or the GitHub Issues Secrets Benchmark.

## Current Harness

- `scripts/benchmark-local.py` measures extraction, scanning, rewrite, and total processing time.
- Cases include small, medium, and large benign prompts, PII, secrets, obfuscated text, tool output, JSON-string arguments, and nested content.
- Outputs are generated under ignored `docs/reports/benchmarks/`.

## Methodology Notes

- The benchmark is a local engineering harness, not a third-party accuracy claim.
- Detector precision and recall are synthetic-fixture only.
- Optional model-backed detectors should be benchmarked separately because model load time, hardware, and cold start dominate latency.

## External Dataset Posture

AI4Privacy PII-Masking-300k and the GitHub Issues Secrets Benchmark are external references only. Review their licenses before any commercial, redistributed, derivative, or training use.
