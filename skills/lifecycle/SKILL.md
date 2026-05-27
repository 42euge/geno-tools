---
name: geno-lifecycle
description: Skill and skillset CRUD — bootstrap a new geno-* repo, scaffold skills inside it, install local checkouts, and inspect ecosystem status.
---

# geno-lifecycle

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the create, install, and inspect operations of the skill development lifecycle.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [repo-create](skills/repo-create/SKILL.md) | `/geno-lifecycle-repo-create` | Bootstrap a new `geno-{name}` skillset repository — directory tree, manifest, docs scaffold, CI templates. |
| [skill-create](skills/skill-create/SKILL.md) | `/geno-lifecycle-skill-create` | Scaffold a new skill inside an existing geno-* repo. Updates the umbrella table and `GENO.md` skills table. |
| [install](skills/install/SKILL.md) | `/geno-lifecycle-install` | Install skills from a local geno ecosystem repo checkout globally via `npx skills add`. |
| [status](skills/status/SKILL.md) | `/geno-lifecycle-status` | Show installation status — version, commit, branch, and freshness — for every installed skillset. |

## When to use this sub-skillset

You're authoring or operating a geno ecosystem repo. Pick the leaf skill that matches the verb:

- **Starting from scratch**: `/geno-lifecycle-repo-create` to scaffold the whole repo.
- **Adding to an existing repo**: `/geno-lifecycle-skill-create` to add a single skill.
- **Testing local changes**: `/geno-lifecycle-install` to register your local checkout globally without publishing.
- **Audit what's installed**: `/geno-lifecycle-status` to see versions, branches, and staleness.
