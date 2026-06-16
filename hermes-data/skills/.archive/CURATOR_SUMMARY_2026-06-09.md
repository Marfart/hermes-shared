# Curator Pass — 2026-06-09 UMBRELLA-BUILDING CONSOLIDATION

## Human Summary

### Consolidations (3 skills merged into umbrella skills)

**1. ip-camera-reconnaissance → camera-reconnaissance**
These two skills were near-duplicates covering the same 3-layer surveillance camera discovery methodology (local USB → LAN IP cameras → public internet OSINT). `camera-reconnaissance` was the English-language version; `ip-camera-reconnaissance` was the Chinese-language version with additional PowerShell detail. Merged the Chinese content (Layer 1 checklists, PowerShell scan scripts, Shodan dorks, key principles) into `camera-reconnaissance` as a new "Complete Scan Flow" section. The old skill's reference files (`camera-port-signatures.md`, `git-bash-powershell-workaround.md`) were moved into `camera-reconnaissance/references/`.

**2. codex → claude-code**
Both skills covered delegating coding tasks to external AI agent CLIs. `claude-code` was the comprehensive umbrella for Anthropic Claude Code CLI; `codex` was a gstack-originated port for OpenAI Codex CLI's three modes (review, challenge, consult). Merged the Codex-specific content (setup, three-mode workflow, integration notes) into `claude-code` as a new "OpenAI Codex CLI Support" section. Now one skill covers all AI coding agent orchestration.

**3. sketch → claude-design**
Both skills about generating HTML/CSS design artifacts. `sketch` was a narrow workflow for "2-3 throwaway HTML mockup variants" — a subset of what `claude-design` already covers as a full design process guide. Merged `sketch`'s unique content (variant axes, intake questions, comparison table, output conventions, interactivity bar) into `claude-design` as a new "Sketch Workflow" section. `claude-design` already referenced `sketch` as a related skill.

### Prunings (8 built-in skills archived, 0 usage ever)

Archived 8 built-in skills that have **0 activity and 0 use** since installation. These are well-known stable features that can be restored on user request via `hermes update`:

- **dogfood** — QA testing workflow, never used
- **blogwatcher** — RSS/feed monitoring, never used
- **maps** — OpenStreetMap geocoding, never used
- **gif-search** — Tenor GIF search, never used
- **jupyter-live-kernel** — Jupyter notebook kernel, never used
- **teams-meeting-pipeline** — Teams meeting pipeline, never used
- **openhue** — Philips Hue control, never used
- **yuanbao** — Yuanbao groups integration, never used

Additionally, 6 built-in manifest-only entries (design-md, google-workspace, nano-pdf, powerpoint, humanizer, polymarket) have no on-disk directories and have 0 activity — they were noted but cannot be physically archived.

### Skills Left Alone (class-level, maintain separation)

- **BLIIoT/B2B cluster (6 skills):** All are well-scoped class-level skills covering different stages of the B2B sales pipeline (acquisition, directory promotion, email, technical research, quotation database, customer scoring). Each addresses a distinct phase of the workflow.
- **Windows security cluster (4 skills):** `windows-edr-evasion` (process-level red team), `windows-network-security-audit` (network/offensive security), `windows-system-forensics` (event log investigation), `windows-health-diagnostics` (system performance). Different domains, already properly categorized.
- **ML/LLM skills:** `llama-cpp`, `huggingface-hub`, `weights-and-biases`, `comfyui` are all class-level ML infrastructure skills with distinct purposes.
- **Dev workflow:** `simplify-code`, `systematic-debugging`, `test-driven-development` are distinct software engineering methodologies, not overlapping.
- **Creative/diagram skills:** `architecture-diagram`, `ascii-art`, `ascii-video`, `excalidraw`, `p5js`, `manim-video`, `songwriting-and-ai-music`, `pretext`, `popular-web-designs` are all distinct creative tools.
- **Self-management:** `hermes-agent`, `self-maintenance`, `daily-briefing-cron`, `autonomous-learning` all have unique non-overlapping purposes.

## Structured summary

```yaml
consolidations:
  - from: ip-camera-reconnaissance
    into: camera-reconnaissance
    reason: Near-identical 3-layer camera discovery methodology (local/LAN/public), one English one Chinese; merged Chinese-specific PowerShell scan scripts and port signatures
  - from: codex
    into: claude-code
    reason: Both cover delegating coding to external AI agent CLIs; codex was OpenAI Codex CLI port of same pattern as claude-code (Anthropic Claude Code)
  - from: sketch
    into: claude-design
    reason: Sketch was a narrow "2-3 HTML mockup variants" workflow, a subset of claude-design's comprehensive design process; claude-design already referenced it

prunings:
  - name: dogfood
    reason: Built-in QA testing skill, 0 activity/use since install, not relevant to current workflow
  - name: blogwatcher
    reason: Built-in RSS/feed monitoring skill, 0 activity/use, no current monitoring need
  - name: maps
    reason: Built-in OSM geocoding/routing skill, 0 activity/use
  - name: gif-search
    reason: Built-in Tenor GIF search skill, 0 activity/use
  - name: jupyter-live-kernel
    reason: Built-in Jupyter notebook kernel skill, 0 activity/use
  - name: teams-meeting-pipeline
    reason: Built-in Teams meeting pipeline skill, 0 activity/use, no Teams integration active
  - name: openhue
    reason: Built-in Philips Hue light control skill, 0 activity/use, no Hue bridge present
  - name: yuanbao
    reason: Built-in Yuanbao groups integration skill, 0 activity/use
```
