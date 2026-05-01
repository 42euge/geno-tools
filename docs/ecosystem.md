# Ecosystem

The geno-\* ecosystem is a collection of repos that extend AI coding agents with specialized capabilities. geno-tools is the agent-agnostic meta package manager at the center: it discovers skills, absorbs external skill systems, evaluates variants via the meta-harness, governs compliance through auditing, and lets capabilities evolve safely.

## Repos

### Core

| Repo | Description |
|------|-------------|
| [geno-tools](https://github.com/42euge/geno-tools) | Meta-CLI and Claude Code plugin — install, update, variant-manage skillsets |
| [geno-agents](https://github.com/42euge/geno-agents) | Multi-agent coordination, registration, autonomous loops |
| [geno-msg](https://github.com/42euge/geno-msg) | Inter-agent messaging |
| [geno-notes](https://github.com/42euge/geno-notes) | Project journal, task management, timestamped notes |
| [geno-mon](https://github.com/42euge/geno-mon) | Agent monitoring |

### Skillsets

| Repo | Description |
|------|-------------|
| [geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts, TTS/STT config |
| [geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| [geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, discussion scraping |
| [geno-dev](https://github.com/42euge/geno-dev) | Developer/infrastructure skills — task execution, commit rewriting, Colab plumbing |

### Runtime and tooling

| Repo | Description |
|------|-------------|
| [geno-cli](https://github.com/42euge/geno-cli) | Agentic coding assistant TUI powered by Gemma 4 via Ollama |
| [geno-iso](https://github.com/42euge/geno-iso) | Isolated Docker containers for running Claude Code |
| [geno-term](https://github.com/42euge/geno-term) | Terminal automation for Claude Code session recovery with iTerm2 tabs and panes |
| [geno-vla](https://github.com/42euge/geno-vla) | Vision-Language-Action MCP server for Claude Code with smart browser automation |
| [geno-bench](https://github.com/42euge/geno-bench) | Mine Claude Code session logs for failure patterns and turn observed failures into benchmark tasks |

## How it fits together

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

## External skill systems

geno-tools absorbs skills from external systems into the unified `SKILL.md` + `genotools.yaml` framework:

- **[Vercel Labs Skills](https://github.com/vercel-labs/skills)** — the backend skill registration layer; `npx skills add` registers skills with all agents
- **[obra/superpowers](https://github.com/obra/superpowers)** — plugin manifest conventions that geno-tools follows for cross-agent compatibility
- **Ralphy Loop** — external plugin ecosystem whose skills can be ingested and normalized through `geno-tools install`

Skills from any of these origins are managed the same way once absorbed: same install path, same variant system, same audit checklist, same removal contract.
