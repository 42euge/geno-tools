---
name: geno-self
description: geno-tools self-management — update the ecosystem, run the self-improvement cycle, spawn new sessions, open the docs site.
---

# geno-self

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering operations that geno-tools performs **on itself or its host environment** — distinct from skill-lifecycle operations on other skillsets ([geno-lifecycle](../lifecycle/SKILL.md)).

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [update](skills/update/SKILL.md) | `/geno-self-update` | Pull latest revisions for every installed skillset and re-register skills. |
| [improve](skills/improve/SKILL.md) | `/geno-self-improve` | Run the self-improvement cycle — health aggregation, retro triage, mining of session transcripts. |
| [session-spawn](skills/session-spawn/SKILL.md) | `/geno-self-session-spawn` | Open a new Claude Code session window in a target workspace directory. |
| [docs-open](skills/docs-open/SKILL.md) | `/geno-self-docs-open` | Open the geno-tools documentation site in the default browser. |

## When to use this sub-skillset

The verbs apply to **the geno-tools install itself**, not to a particular skill or repo:

- **Sync to latest**: `/geno-self-update`
- **Trigger self-improvement loop**: `/geno-self-improve`
- **Branch into a fresh session**: `/geno-self-session-spawn <workspace>`
- **Find documentation**: `/geno-self-docs-open`
