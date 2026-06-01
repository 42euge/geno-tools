---
name: geno-lifecycle
description: Skill and skillset authoring — bootstrap a new geno-* repo, scaffold skills inside it, and onboard new sources.
---

# geno-lifecycle

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the authoring and onboarding operations of the skill development lifecycle. For installing or inspecting already-authored skillsets, see [geno-manager](../manager/SKILL.md).

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [repo-create](skills/repo-create/SKILL.md) | `/geno-lifecycle-repo-create` | Bootstrap a new `geno-{name}` skillset repository — directory tree, manifest, docs scaffold, CI templates. |
| [skill-create](skills/skill-create/SKILL.md) | `/geno-lifecycle-skill-create` | Scaffold a new skill inside an existing geno-* repo. Updates the umbrella table and `GENO.md` skills table. |
| [onboarding-public](skills/onboarding-public/SKILL.md) | `/geno-lifecycle-onboarding-public` | Discover existing `geno-*` repos under the user's GitHub account, or guide them through creating one, then admit it to the public registry. |
| [onboarding-enterprise](skills/onboarding-enterprise/SKILL.md) | `/geno-lifecycle-onboarding-enterprise` | Discover existing `{company-slug}-*` enterprise prefixes already in use, or guide a platform team through picking a new prefix and bootstrapping the first repo. Supports GitHub Enterprise / GitLab / Bitbucket / Gitea. |

## When to use this sub-skillset

You're authoring a new geno ecosystem repo or skill, or onboarding a new source. Pick the leaf skill that matches the verb:

- **Starting from scratch**: `/geno-lifecycle-repo-create` to scaffold the whole repo.
- **Adding to an existing repo**: `/geno-lifecycle-skill-create` to add a single skill.
- **Onboarding a public skillset**: `/geno-lifecycle-onboarding-public` to find your existing `geno-*` repos (or bootstrap one) and admit it to the public registry.
- **Onboarding an enterprise skillset**: `/geno-lifecycle-onboarding-enterprise` to discover existing `{company-slug}-*` prefixes (or stand up a new one) via discovery sources.
