---
name: geno-compliance
description: Compliance gate for geno-* skillsets — onboard new skill sources and audit existing repos against ecosystem conventions.
---

# geno-compliance

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the safety and admission gate that every skillset passes through before it joins the ecosystem. Implements the **govern** stage of the meta-harness loop documented in [VISION.md](../../VISION.md).

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [audit](skills/audit/SKILL.md) | `/geno-compliance-audit` | Audit a geno-ecosystem repo for compliance with skillset conventions. Tiered required/recommended/optional checklist; rules live in `audit/rules/`. |
| [onboarding](skills/onboarding/SKILL.md) | `/geno-compliance-onboarding` | Walk an operator through onboarding a new skillset — public registry, enterprise namespace, or direct URL. Includes discovery from GitHub Enterprise, GitLab, Bitbucket, Gitea. |

## When to use this sub-skillset

- **New skill source**: `/geno-compliance-onboarding` walks you through admitting a repo into a namespace.
- **Existing skill source**: `/geno-compliance-audit` checks an installed or candidate repo against the ecosystem conventions.

Both skills are gates, not optional add-ons — every ingestion path (registry PR, enterprise namespace, direct URL install) must pass through them per [TENETS.md](../../TENETS.md) tenet 3 (Auditing as infrastructure).
