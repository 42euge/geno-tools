---
name: geno-tools
description: >-
  Skills catalog for the geno ecosystem.
  Use when users ask about this repo, skill catalogs, or onboarding
  a new skillset into the broader geno installation flow.
allowed-tools: "Bash(geno-tools *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-tools — Skill Catalog

This repo is a skills-only catalog and plugin package. It exposes skill commands that help discover and manage geno ecosystem skills.

## Available Skillsets

These are referenced from the skill catalog:

| Repo | Description |
|------|-------------|
| geno-agents | Agent coordination, presence, and multi-agent networking |
| geno-media | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| geno-research | Wiki-based research notes, paper generation, repo docs |
| geno-kaggle | Kaggle benchmarks, competition notebooks, discussion scraping |
| geno-dev | Developer utilities, Colab uploads, commit rewriting |

## Infrastructure Skills

| Skill | Description |
|-------|-------------|
| geno-alias | Create, remove, and list custom slash-command aliases |
| geno-audit | Audit a geno-ecosystem repo for compliance with skillset conventions |
| geno-data-workspaces-init | Create data workspaces for personal/life skills (taxes, remodel, career) |
| geno-icons | Generate pixel-art icons for geno ecosystem repos |
| geno-onboarding | Onboarding wizard for new geno ecosystem skillsets |
| geno-skills-create | Scaffold a new skill in a geno ecosystem repo |
| geno-tools-create-skillset-repo | Scaffold a new geno ecosystem skillset repo from scratch |
| geno-skills-install | Install skills from a local repo checkout globally |
| geno-skills-status | Show version, commit, and freshness of installed skillsets |
| geno-tools-improve | Run the self-improvement cycle — health report, retro triage, session mining |
| geno-tools-open-docs | Open the geno-tools documentation site |
| geno-tools-update | Pull the latest version of installed skillsets and re-register with all agents |

## Note

This repo does not include the local `geno-tools` Python CLI runtime. If users need full install/update/remove workflows, they should use the external CLI package provided by the ecosystem's install path.
