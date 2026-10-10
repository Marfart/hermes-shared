---
name: llm-safety-evaluation
description: "Use for authorized LLM safety testing."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [llm, safety, evaluation, red-team, prompt-injection, robustness]
    category: red-teaming
---

# LLM Safety Evaluation (Defensive)

A controlled workflow for measuring whether an authorized model or agent follows its intended safety and tool-use rules. Godmode-style attack families may inform the *risk taxonomy*, but this skill does not generate, optimize, or run jailbreak payloads.

## When to Use

Use for an authorized safety or robustness assessment of a model or agent you own or have explicit permission to test. Use the benign matrix and local scorer; do not use this skill to bypass a hosted model's safeguards.

This workflow is the default behavioral standard for Godmode-related research and LLM safety testing: establish scope first, use harmless synthetic cases and local scoring, distinguish verified findings from assumptions, and stop or redirect requests that turn into safeguard bypass or real-world actions.

## Hard gates

1. Test only a model, endpoint, account, and dataset you own or are explicitly authorized to assess. Record the authorization and scope before testing.
2. Do not create or refine prompts intended to defeat a hosted model's safeguards. Do not use automated attack search, stealth/obfuscation recipes, refusal-suppression scoring, or multi-turn escalation campaigns.
3. Use synthetic canary strings only. Never put real system prompts, API keys, customer data, personal data, or confidential material into prompts, logs, or third-party testing services.
4. Keep tools mocked or read-only. No external messages, purchases, account changes, shell execution, or network actions during evaluation.
5. If any test unexpectedly elicits sensitive or actionable content, stop the run, redact the output, and report the case ID and category rather than reproducing the content.

## Workflow

1. **Scope:** Record target/model version, provider, test date, permitted tools, policy version, endpoint owner, data handling, and stop conditions. Do not infer authorization from API access alone.
2. **Baseline:** Include ordinary safe requests to measure helpfulness and detect over-refusal.
3. **Harmless robustness cases:** Use `references/eval-matrix.md`. Test instruction hierarchy with synthetic data, prompt injection embedded in inert documents, fake canary protection, conversation-state consistency, tool authorization using mocks, and safe-request over-refusal.
4. **Freeze the set:** Give every case a stable ID and version. Do not let the tested model or an attacker model mutate prompts during the run. Keep expected behavior independent of model output.
5. **Run narrowly:** Start with a small pilot, low request volume, and fixed settings. Stop on unexpected sensitive output, provider warning, cost limit, or scope breach.
6. **Score:** Save model outputs only if the authorization and data policy permit. Run `scripts/score_safety_eval.py` over a redacted JSONL result file. This is a heuristic report, not a substitute for human review.
7. **Review:** Have a human review all flagged cases and a sample of unflagged cases. Separate false refusal, unsafe compliance, canary exposure, and unauthorized tool use; do not combine them into a single “more compliant is better” score.
8. **Report:** Include scope, model/version, test-set revision, aggregate metrics, representative benign case IDs, limitations, and remediation suggestions. Do not publish prompts or outputs that expose safeguards or sensitive data.

## Metrics

- **Safe-answer rate:** expected-answer cases not classified as refusals. Review correctness separately.
- **Refusal detection rate:** expected-refusal cases classified as refusals. Human-check the heuristic.
- **Over-refusal rate:** expected-answer cases classified as refusals.
- **Canary exposure:** exact synthetic canary found in output.
- **Unauthorized tool-call rate:** calls outside the case's explicit allowlist.
- **Consistency:** same policy decision across equivalent, versioned benign cases.

A refusal is not inherently a failed result. The expected behavior must be set from the authorized evaluation rubric before the run. Never reward response length, vividness, or actionability as a proxy for safety.

## Local scorer

The standard-library-only scorer consumes completed, redacted model results; it does not call a model, create prompts, or send requests. Example:

```bash
python scripts/score_safety_eval.py templates/sample_results.jsonl
python -m unittest scripts/test_score_safety_eval.py
```

Input schema and caveats are in `references/eval-matrix.md`.

## Source notes

- Use the current GitHub main branch and official project terms as source material; do not assume a release tag exists.
- OpenAI Evals treats Safety, Over-refusals, and System-message steerability as distinct evaluation categories; version datasets and human-check grader labels.
- The installed `godmode` skill is attack-oriented and includes refusal-suppression scoring. Do not reuse that scoring objective for defensive evaluation.
- Review third-party test tooling's telemetry and provider data handling before sending any prompt to it. Use synthetic cases and a local or explicitly approved endpoint.
