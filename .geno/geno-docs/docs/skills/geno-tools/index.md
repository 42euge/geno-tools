---
title: geno-tools
description: Meta-CLI — install, update, and manage skillsets across all agents
---

# geno-tools

Meta-CLI — install, update, and manage skillsets across all agents.

[:material-github: GitHub](https://github.com/42euge/geno-tools){ .md-button }

Skills are organized into 6 functional sub-skillsets. The full naming and layout convention is in [Upstream Conventions](../../skillsets/upstream-conventions.md).

## Sub-skillsets

| Area | Slash command | Skills |
|------|---------------|--------|
| [lifecycle](lifecycle/index.md) | `/geno-lifecycle` | repo-create, skill-create, onboarding-public, onboarding-enterprise — skill & skillset authoring |
| [manager](manager/index.md) | `/geno-manager` | install, status — package management of installed skillsets |
| [compliance](compliance/index.md) | `/geno-compliance` | audit — admission gate to the ecosystem |
| [self](self/index.md) | `/geno-self` | update, improve, session-spawn — geno-tools self-management |
| [assets](assets/index.md) | `/geno-assets` | icons — generated branding assets |
| [config](config/index.md) | `/geno-config` | alias — user personalization |

## Slash command renames (from 0.2.0)

Version 0.3.0 re-architected the skill tree by intent. Slash commands renamed:

| Old | New |
|-----|-----|
| `/geno-skills-create` | `/geno-lifecycle-skill-create` |
| `/geno-skills-install` | `/geno-manager-install` |
| `/geno-skills-status` | `/geno-manager-status` |
| `/geno-tools-create-skillset-repo` | `/geno-lifecycle-repo-create` |
| `/geno-audit` | `/geno-compliance-audit` |
| `/geno-onboarding` (public) | `/geno-lifecycle-onboarding-public` |
| `/geno-onboarding` (enterprise) | `/geno-lifecycle-onboarding-enterprise` |
| `/geno-tools-update` | `/geno-self-update` |
| `/geno-tools-improve` | `/geno-self-improve` |
| `/geno-tools-sessions-spawn` | `/geno-self-session-spawn` |
| `/geno-data-workspaces-init` | `/geno-ws-data-init` (moved to geno-ws skillset) |
| `/geno-icons` | `/geno-assets-icons` |
| `/geno-alias` | `/geno-config-alias` |
| `/geno-tools` | unchanged (umbrella) |

To preserve old muscle memory, set up aliases via `/geno-config-alias add <old> <new>`.

## CLI commands

- `geno-tools ls` — list installed skillsets and their active variant
- `geno-tools ls --available` — show all registered skillsets in the registry
- `geno-tools install <repo|url|path>` — install a skillset (clone, venv, register with all agents)
- `geno-tools remove <repo> [--keep-data]` — uninstall a skillset from all agents
- `geno-tools update [repo]` — pull latest for one or all skillsets
- `geno-tools doctor` — verify symlinks, worktrees, venvs

## Available skillsets

Install by full repo name (e.g. `geno-tools install geno-<name>`):

| Repo | Description |
|------|-------------|
| geno-agents | Agent coordination, presence, and multi-agent networking |
| geno-media | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| geno-research | Wiki-based research notes, paper generation, repo docs |
| geno-kaggle | Kaggle benchmarks, competition notebooks, discussion scraping |
| geno-dev | Developer utilities, Colab uploads, commit rewriting |

## Source resolution

The `<repo>` argument resolves in order:

1. Registered repo name (e.g. `geno-<name>`) → git URL. Bare slug (e.g. `<name>`) is also accepted for backwards compatibility.
2. Local directory path
3. Git URL (https:// or git@)
