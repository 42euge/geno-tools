---
name: geno-compliance
description: Compliance gate for geno-* skillsets — audit existing repos against ecosystem conventions before they join the ecosystem.
---

# geno-compliance

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the safety and admission audit that every skillset passes through before it joins the ecosystem. Implements the **govern** stage of the meta-harness loop documented in [VISION.md](../../VISION.md).

Onboarding (the operator workflow that drives a candidate repo through the audit gate) lives in the lifecycle sub-skillset as two sibling skills: [`/geno-lifecycle-onboarding-public`](../lifecycle/skills/onboarding-public/SKILL.md) for the curated public registry, and [`/geno-lifecycle-onboarding-enterprise`](../lifecycle/skills/onboarding-enterprise/SKILL.md) for `{company-slug}-*` namespaces with discovery.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [audit](skills/audit/SKILL.md) | `/geno-compliance-audit` | Audit a geno-ecosystem repo for compliance with skillset conventions. Tiered required/recommended/optional checklist; rules live in `audit/rules/`. |

## When to use this sub-skillset

- **Existing skill source**: `/geno-compliance-audit` checks an installed or candidate repo against the ecosystem conventions.

The audit is a gate, not an optional add-on — every ingestion path (registry PR, enterprise namespace, direct URL install) must pass through it per [TENETS.md](../../TENETS.md) tenet 3 (Auditing as infrastructure).
