---
name: geno-manager
description: Package management for installed geno-* skillsets — install local checkouts globally and inspect the installed ecosystem.
---

# geno-manager

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering package-manager operations on already-authored skillsets: installing them and inspecting what is installed.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [install](skills/install/SKILL.md) | `/geno-manager-install` | Install skills from a local geno ecosystem repo checkout globally via `npx skills add`. |
| [status](skills/status/SKILL.md) | `/geno-manager-status` | Show installation status — version, commit, branch, and freshness — for every installed skillset. |

## When to use this sub-skillset

You're managing the set of skillsets installed on a machine, not authoring new ones. Pick the leaf skill that matches the verb:

- **Testing local changes**: `/geno-manager-install` to register your local checkout globally without publishing.
- **Audit what's installed**: `/geno-manager-status` to see versions, branches, and staleness.

For authoring (creating a new skillset repo or scaffolding a new skill inside one), see [geno-lifecycle](../lifecycle/SKILL.md).
