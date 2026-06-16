# Skills Update: Name Collision Resolution

When running `hermes skills update`, skills stored in the hub-based lockfile
(`~/.hermes/skills/.hub/manifest.lock`) that share a name with another skill
from a different source will fail to auto-update and present a table of
candidates instead.

## Symptom

```
Updating: notion
Resolving 'notion'...

Multiple skills named 'notion' found:
┌───────────┬───────────┬─────────────────────────────────────────────────┐
│ Source    │ Trust     │ Identifier                                      │
├───────────┼───────────┼─────────────────────────────────────────────────┤
│ skills.sh │ community │ skills-sh/steipete/clawdis/notion               │
│ skills.sh │ community │ skills-sh/membranedev/application-skills/notion │
└───────────┴───────────┴─────────────────────────────────────────────────┘
Use the full identifier to install a specific one.
```

(Example from June 2026 on a Hermes v0.15.x install.)

## Root Cause

The hub manifest (`manifest.lock`) stores skills by name. When two or more
hub skills from different sources (e.g. two different community repos on
skills.sh) share the same name, `hermes skills update` cannot determine which
one the user intended. The update is skipped and the user must resolve it
manually with the full identifier chain.

## Resolution

1. Identify the currently installed version by checking the lockfile:
   ```bash
   grep -A3 '"notion"' ~/AppData/Local/hermes/skills/.hub/manifest.lock
   ```

2. Re-install using the full identifier:
   ```bash
   hermes skills install skills-sh/steipete/clawdis/notion
   ```

3. The full identifier is the third column in the update prompt's table.

## Which Skills Are Prone to Collisions

Rare — collisions occur only when:
- Multiple community repos on skills.sh publish a skill with the same name
- The skill name is a common word ("notion", "arxiv", "docker")

Official/builtin skills never collide because they use a different namespace
prefix (`official/*`, `builtin/*`).

## Prevention

During `hermes skills update`, the process is non-interactive — failed
collision-resolutions simply print a warning and continue to the next skill.
The skill that hit the collision is left at its previous version. This is
a known limitation and does not block other skill updates.