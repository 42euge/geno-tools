---
name: geno-tools
description: >-
  Meta-CLI for installing and managing geno-* skillsets.
  Use when user says /geno-tools-install, /geno-tools-remove, /geno-tools-ls, /geno-tools-update, /geno-tools-repos-scaffold,
  /geno-tools-icons-generate, or asks about installing/removing/listing/creating geno ecosystem skillsets.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m genotools *)"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Manages installation, removal, and updates of skillset repos.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. Install: pipx install git+https://github.com/42euge/geno-tools.git"
```

## Available Skillsets

| Name | Description |
|------|-------------|
| agents | Agent coordination, presence, and multi-agent networking |
| media | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| research | Wiki-based research notes, paper generation, repo docs |
| taxes | Tax document parsing, CPA packet prep |
| kaggle | Kaggle benchmarks, competition notebooks, discussion scraping |
| dev | Developer utilities, Colab uploads, commit rewriting |
| iso | Isolated Docker containers for running Claude Code |

## Commands

- `geno-tools ls` — list installed skillsets and their active variant
- `geno-tools ls --available` — show all registered skillsets in the registry
- `geno-tools install <name|url|path>` — install a skillset (clone, venv, register with all agents)
- `geno-tools remove <name> [--keep-data]` — uninstall a skillset from all agents
- `geno-tools update [name]` — pull latest for one or all skillsets
- `geno-tools doctor` — verify symlinks, worktrees, venvs

## Source Resolution

The `<name>` argument resolves in order:
1. Registry short name (e.g. `media`) -> git URL
2. Local directory path
3. Git URL (https:// or git@)
