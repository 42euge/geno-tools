# Skill Reference

This repo is skills-only. There is no local Python CLI binary to call directly.

The usable entry points are slash commands exposed by supported agents after plugin install.

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| geno-tools | `/geno-tools` | Overview of the `geno-tools` skillset and other skills included here |
| geno-onboarding | `/geno-onboarding` | Walk an operator through skillset onboarding workflows |
| geno-skills-install | `/geno-skills-install` | Register skills from a local checkout |
| geno-skills-create | `/geno-skills-create` | Scaffold a new SKILL.md in a repo |
| geno-skills-status | `/geno-skills-status` | Show installed skillset versions and status |
| geno-tools-update | `/geno-tools-update` | Update installed geno ecosystem skillsets |
| geno-tools-open-docs | `/geno-tools-open-docs` | Open this documentation site |

If you need `geno-tools install`, `geno-tools ls`, etc., use the external CLI package from the ecosystem install path rather than this repo.
