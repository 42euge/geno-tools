# Ecosystem

The geno-\* ecosystem is a collection of repos that extend AI coding agents with specialized capabilities. geno-tools is the package manager; each skill is its own repo.

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

### Other

| Repo | Description |
|------|-------------|
| [geno-bot](https://github.com/42euge/geno-bot) | Bluesky companion bot (geno42) |
| [geno-colab](https://github.com/42euge/geno-colab) | Google Colab integration |
| [geno-bench](https://github.com/42euge/geno-bench) | Benchmarking infrastructure |
| [geno-term](https://github.com/42euge/geno-term) | Terminal utilities |
| [geno-vla](https://github.com/42euge/geno-vla) | Vision-language-action experiments |
| [obsidian-geno-claude](https://github.com/42euge/obsidian-geno-claude) | Obsidian plugin for Claude integration |
| [obsidian-genovox](https://github.com/42euge/obsidian-genovox) | Obsidian voice plugin |

## How it fits together

```
                    geno-tools (package manager)
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     geno-media    geno-research   geno-kaggle  ...
          │              │              │
          └──────────────┼──────────────┘
                         │
                   Coding CLIs
                   (Claude Code, geno-cli, Codex, Gemini CLI)
                         │
                    geno-agents (coordination)
                    geno-msg    (messaging)
                    geno-notes  (project state)
                    geno-mon    (monitoring)
```

Each skillset is independent — install only what you need. The coordination layer (agents, msg, notes, mon) is optional but enables multi-agent workflows.
