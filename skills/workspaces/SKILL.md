---
name: geno-workspaces
description: Data workspace scaffolding — initialize directories with metadata, agent context, and links to related workspaces for personal and life skills.
---

# geno-workspaces

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the creation and configuration of **data workspaces** — typed directories that hold the artifacts and per-workspace agent context for personal/life skills (taxes, career, remodel, custom).

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [data-init](skills/data-init/SKILL.md) | `/geno-workspaces-data-init` | Scaffold a new data workspace — directory layout, metadata file, agent rules, registry entry. |

## When to use this sub-skillset

You're starting work on a personal/life domain (taxes for the year, a remodel project, a career campaign) and want a structured directory with agent-aware context. Run `/geno-workspaces-data-init` and pick the workspace type.

This sub-skillset has room to grow — future leaves could include `data-migrate`, `data-archive`, or domain-specific scaffolds.
