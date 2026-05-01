---
name: geno-tools
description: >-
  Meta-CLI for installing and managing geno-* skillsets.
  Use when user asks about installing, removing, listing, or updating
  geno ecosystem skillsets.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m genotools *)"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Manages installation, removal, and updates of skillset repos.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. The plugin's SessionStart hook (Claude Code) and OpenCode plugin loader run scripts/bootstrap.sh automatically. On Gemini CLI / Codex / Cursor, run 'bash \$PLUGIN_ROOT/scripts/bootstrap.sh' once (\$PLUGIN_ROOT is e.g. ~/.gemini/extensions/geno-tools)."
```

## Available Skillsets

Install by full repo name (e.g. `geno-tools install geno-<name>`):

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
| geno-data-workspaces-init | Create data workspaces for personal/life skills (taxes, remodel, career) |
| geno-skills-create | Scaffold a new skill in a geno ecosystem repo |

## Commands

- `geno-tools ls` — list installed skillsets and their active variant
- `geno-tools ls --available` — show all registered skillsets in the registry
- `geno-tools install <repo|url|path>` — install a skillset (clone, venv, register with all agents)
- `geno-tools remove <repo> [--keep-data]` — uninstall a skillset from all agents
- `geno-tools update [repo]` — pull latest for one or all skillsets
- `geno-tools doctor` — verify symlinks, worktrees, venvs

## Source Resolution

The `<repo>` argument resolves in order:
1. Registered repo name (e.g. `geno-<name>`) -> git URL. Bare slug (e.g. `<name>`) is also accepted for backwards compatibility.
2. Local directory path
3. Git URL (https:// or git@)
