---
name: geno-assets
description: Generated branding and visual assets for the geno ecosystem — pixel-art icons, badges, and other regenerable artifacts.
---

# geno-assets

Sub-skillset of [geno-tools](../geno-tools/SKILL.md) covering the generation and refresh of **regenerable visual assets** that ship alongside skillsets — anything an artist would normally produce by hand but that a model can produce reproducibly from a prompt and a fixed pipeline.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| [icons](skills/icons/SKILL.md) | `/geno-assets-icons` | Generate or refine pixel-art icons for geno-* repos using SD 1.5 + a pixel-art LoRA. |

## When to use this sub-skillset

You're shipping a new geno-* skillset and need a project icon, or refreshing existing icons after a visual style update. Run `/geno-assets-icons` and pick generate/refine/status.

Future leaves may include `badges`, `logos`, or `social-cards` — anything that fits the "deterministic regeneration from a prompt + reference style" pattern.
