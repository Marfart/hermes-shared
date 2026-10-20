---
name: github
description: "Use when researching GitHub repositories; verify source and results."
version: 2.0.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, gh, git, pull-requests, issues, code-review, repos, auth, ci]
    category: software-development
    related_skills: [codebase-inspection, requesting-code-review]
---

# GitHub

Work GitHub end to end with the `gh` CLI (REST fallback where noted): auth,
issues, the PR lifecycle, issue-to-PR delivery, code review, and repo
management. This skill consolidates six former skills; each workflow lives
complete in its reference file — ALWAYS read the matching reference before
starting that workflow, the body below only routes.

## Routing

| Task | Read first |
|---|---|
| Auth broken / new machine / token or SSH setup / gh login | `references/auth.md` |
| Create, triage, label, assign, close issues | `references/issues.md` |
| Branch, commit, open PR, watch CI, merge | `references/pr-workflow.md` |
| Carry an ISSUE to a verified PR (full delivery loop) | `references/issue-to-pr.md` |
| Review someone's PR: diffs, inline comments, verdict | `references/code-review.md` |
| Clone/create/fork repos, remotes, releases | `references/repo-management.md` |

Supporting assets: `scripts/gh-env.sh` + `scripts/git-credential-token.py`
(auth helpers), `templates/` (PR bodies, bug report, feature request),
`references/ci-troubleshooting.md`, `references/conventional-commits.md`,
`references/github-api-cheatsheet.md`, `references/review-output-template.md`.

## Core discipline (applies to every workflow)

- Preflight once per session: `gh auth status` — if it fails, go to
  `references/auth.md` before anything else.
- Prefer `gh` over raw REST; drop to `gh api` only for endpoints the
  porcelain lacks (the cheatsheet lists them).
- Never report CI green without checking `gh pr checks` yourself; never
  claim merged without verifying `state,mergedAt`.
- Read full context before writing: `gh issue view --comments` /
  `gh pr view --comments` — decisions live in threads, not titles.
- Sweep for duplicates before creating anything:
  `gh pr list --search` / `gh issue list --search`.
- When exploring repositories for a user's use case, verify the repository identity, platform support, setup prerequisites, maintenance signals, license, and permission/security model before recommending it; match the recommendation to the user's actual OS and intended scope.
- Label recommendations as candidates unless you actually installed and exercised them. Do not imply a project controls the user's bot or machine until its deployment and end-to-end behavior are verified.
- Before committing in a mixed-use or shared repository, inspect the worktree and stage only explicit intended paths; avoid repository-root `git add -A`. Verify the cached path list and abort if it contains anything outside the task allowlist. After push, compare the remote branch OID with local `HEAD` before claiming synchronization succeeded.

## Deep project study

For a request to deeply study GitHub projects (especially with progress reports), follow this sequence:

1. **Scope the study.** Select a small, relevant set of repositories across the requested domains; use stars only for discovery, not as evidence of quality. Check repository metadata (owner/name, archived state, license, recent activity, language/platform) and the project's own contribution/development instructions before choosing files or test commands. If `gh search repos` is unexpectedly empty, broaden the query or use public GitHub API reads; do not treat an empty search as proof no projects exist.
2. **Use an isolated checkout.** Clone upstream into a task-specific working directory, keep experiments outside the clone, and leave upstream files unchanged. Inspect status before and after tests. Avoid system-wide installs, services, production devices, customer systems, or external side effects unless explicitly authorized.
3. **Read implementation, not only the README.** Trace a representative end-to-end behavior through at least three relevant implementation/config/test files. Record file paths and symbols, then explain the design trade-off (why the code behaves this way), not just its feature list. Verify license, maintenance and security/permission claims from authoritative repository files or GitHub metadata.
4. **Exercise a narrow claim.** Prefer the project's existing targeted tests. Add a small original probe in the study directory when it can safely test a design claim; run it and preserve the actual output. Capture exit status and test counts from the command output. Never infer a passing test count from exit code alone, and never describe a source-level inference as a product/device validation.
5. **Translate to the user's use case carefully.** Separate verified repository facts from application hypotheses. For company product relevance, identify what still needs validation against the product's firmware, hardware, supported packages, or engineering documentation; do not turn a plausible integration into a customer-facing capability claim.
6. **Report and preserve progress.** For each requested hourly checkpoint, record the actual local timestamp, files/symbols studied, experiment/test command and exact result, practical relevance, unresolved questions, and next concrete step. Write the report/log before sending the update. A scheduled run proves only that it is scheduled until its run and delivery are verified; do not imply a full hour of active work when the run covered only a shorter checkpoint. For overnight work, use a finite repeating schedule matching the requested number of rounds, then verify the job is enabled, its next run and destination. Mention material model/token cost when known.
7. **Make the result reusable.** Save substantive learning notes in the user's established knowledge workspace and reusable probes under the designated task/script directory; keep secrets and customer data out of reports. Finish with a concise status that distinguishes completed, verified, inferred, and pending work.

## Verification

- The workflow's own reference file defines done for that task.
- Cross-cutting: every claim about remote state (CI, merge, release,
  issue state) is backed by a fresh `gh` read, never memory.
