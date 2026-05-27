---
name: geno-config
description: User personalization for the geno ecosystem — slash-command aliases and other per-user configuration that lives in `~/.geno/config.yaml`.
---

# geno-config

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering **user-level configuration** — preferences that are personal to the operator and live in `~/.geno/config.yaml`, distinct from skillset-level configuration in each repo's `genotools.yaml`.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [alias](skills/alias/SKILL.md) | `/geno-config-alias` | Create, remove, and list custom slash-command aliases for geno ecosystem skills. |

## When to use this sub-skillset

- **Shorter slash commands**: `/geno-config-alias add lci geno-lifecycle-skill-create` so you can type `/lci` instead.
- **Audit aliases**: `/geno-config-alias list` to see what shortcuts you've defined.
- **Cleanup**: `/geno-config-alias remove <name>` to undo.

Future leaves may include `profile` (per-machine identity), `prefix` (global command-prefix swap, currently a static `~/.geno/config.yaml` field), or `reset` (clean restore of defaults).
