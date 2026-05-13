---
title: Ecosystem
description: The geno-* ecosystem at a glance
---

# Ecosystem

The geno ecosystem spans **17 skillsets** and **77 skills**.

Browse the full [Skill Catalog](skills/index.md) or explore individual skillsets below.

## Skillsets

| Skillset | Category | Skills | Description |
|----------|----------|--------|-------------|
| [geno-agents](skills/geno-agents/index.md) | :material-cube-outline: Core | 2 | Multi-agent coordination, registration, autonomous loops |
| [geno-career](skills/geno-career/index.md) | :material-home-outline: Life | 4 | Career toolkit — job search, resume building, application tracking |
| [geno-dev](skills/geno-dev/index.md) | :material-code-braces: Developer | 18 | Developer utilities — commits, worktrees, workspaces, feature shipping |
| [geno-iso](skills/geno-iso/index.md) | :material-cog-outline: Runtime | 6 | Docker containers for isolated Claude Code environments |
| [geno-kaggle](skills/geno-kaggle/index.md) | :material-chart-bar: Data & Research | 6 | Kaggle benchmarking, notebook upload, discussion scraping |
| [geno-loops](skills/geno-loops/index.md) | :material-code-braces: Developer | 7 | Agentic execution loop patterns — cruise, turbocharge, autopilot |
| [geno-mine](skills/geno-mine/index.md) | :material-wrench-outline: Tooling | 3 | Session mining — extract, analyze, and export agent session data |
| [geno-mon](skills/geno-mon/index.md) | :material-cube-outline: Core | 0 | Agent observability and monitoring |
| [geno-msg](skills/geno-msg/index.md) | :material-cube-outline: Core | 0 | Inter-agent messaging |
| [geno-notes](skills/geno-notes/index.md) | :material-cube-outline: Core | 4 | Project journal, task management, wiki, and site generation |
| [geno-research](skills/geno-research/index.md) | :material-chart-bar: Data & Research | 5 | Wiki-based research, paper generation, repo documentation |
| [geno-specs](skills/geno-specs/index.md) | :material-code-braces: Developer | 5 | Execution specifications — create, validate, run, and review |
| [geno-taxes](skills/geno-taxes/index.md) | :material-home-outline: Life | 5 | Tax filing — document parsing, checklists, CPA packet prep |
| [geno-term](skills/geno-term/index.md) | :material-cog-outline: Runtime | 1 | Terminal automation and session recovery |
| [geno-tools](skills/geno-tools/index.md) | :material-cube-outline: Core | 10 | Meta-CLI — install, update, and manage skillsets across all agents |
| [geno-voice](skills/geno-voice/index.md) | :material-palette-outline: Creative | 0 | Voice pipeline |
| [geno-ws](skills/geno-ws/index.md) | :material-cog-outline: Runtime | 1 | Workspace management |

## Architecture

```
        ┌──────────────────────────────────────┐
        │          geno-tools                   │
        │    (meta package manager)             │
        └──────────────┬───────────────────────-┘
                       │
  discover ──→ absorb ──→ evaluate ──→ govern ──→ evolve
     │            │          │            │          │
registry.py    install    fork/use    geno-audit  promote
discovery.py   normalize  worktrees   audit.md    merge → main
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   geno-<name>   geno-<name>   geno-<name>  ...
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Coding CLIs
     (Claude Code, Codex, Gemini CLI, Cursor, OpenCode)
                       │
            geno-agents (coordination)
            geno-msg    (messaging)
            geno-notes  (project state)
            geno-mon    (monitoring)
```

Each skillset is independent — install only what you need. The coordination layer (agents, msg, notes, mon) is optional but enables multi-agent workflows.
