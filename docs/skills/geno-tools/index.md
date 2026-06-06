---
title: geno-tools
description: Meta-CLI — install, update, and manage skillsets across all agents
---

# geno-tools

Meta-CLI — install, update, and manage skillsets across all agents

[:material-github: GitHub](https://github.com/42euge/geno-tools){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-alias](geno-alias.md) | `/geno-alias` | Create, remove, and list custom slash-command aliases for geno ecosystem skills |
| [geno-audit](geno-audit.md) | `/geno-audit` | Audit a geno-ecosystem repo for compliance with skillset conventions |
| [geno-data-workspaces-init](geno-data-workspaces-init.md) | `/geno-data-workspaces-init` | Create data workspaces for personal/life skills (taxes, remodel, career, custom) |
| [geno-icons](geno-icons.md) | `/geno-icons` | Generate pixel art icons for geno-ecosystem projects using SD 1 |
| [geno-onboarding](geno-onboarding.md) | `/geno-onboarding` | Walks an operator through onboarding a new skillset into a geno-tools install, including enterprise discovery from Gi... |
| [geno-skills-create](geno-skills-create.md) | `/geno-skills-create` | Scaffold a new skill in a geno ecosystem repo |
| [geno-skills-install](geno-skills-install.md) | `/geno-skills-install` | Install skills from a local geno ecosystem repo checkout globally via npx skills add |
| [geno-skills-status](geno-skills-status.md) | `/geno-skills-status` | Show the installation status of the geno ecosystem |
| [geno-tools-open-docs](geno-tools-open-docs.md) | `/geno-tools-open-docs` | Open the current repo's GitHub Pages documentation site in the default browser |
| [geno-tools-sessions-spawn](geno-tools-sessions-spawn.md) | `/geno-tools-sessions-spawn` | Spawn a named Claude Code session in a new Terminal window with remote-control enabled and an initial briefing |
| [geno-tools-update](geno-tools-update.md) | `/geno-tools-update` | Update installed geno ecosystem skillsets to the latest main branch |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-tools — Skillset Manager
    
    Orchestrator for the geno-* ecosystem. Manages installation, removal, and updates of skillset repos.
    
    ```!
    which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. The plugin's SessionStart hook (Claude Code) and OpenCode plugin loader run scripts/bootstrap.sh automatically. On Antigravity CLI / Codex / Cursor, run 'bash \$PLUGIN_ROOT/scripts/bootstrap.sh' once (\$PLUGIN_ROOT is e.g. ~/.gemini/antigravity-cli/plugins/geno-tools)."
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
    | geno-alias | Create, remove, and list custom slash-command aliases |
    | geno-data-workspaces-init | Create data workspaces for personal/life skills (taxes, remodel, career) |
    | geno-skills-create | Scaffold a new skill in a geno ecosystem repo |
    | geno-skills-install | Install skills from a local repo checkout globally |
    | geno-skills-status | Show version, commit, and freshness of installed skillsets |
    
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
