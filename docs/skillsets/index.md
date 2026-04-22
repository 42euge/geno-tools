# Skillsets

A **skillset** is a self-contained repo that adds capabilities to an AI coding agent. Each skillset ships a `genotools.yaml` manifest declaring what to set up; geno-tools handles the rest.

## Registry

These skillsets are built into the geno-tools registry and can be installed by short name:

| Name | Repo | Description |
|------|------|-------------|
| `agents` | [geno-agents](https://github.com/42euge/geno-agents) | Agent coordination, registration, status updates, autonomous loops |
| `media` | [geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts, TTS/STT |
| `research` | [geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| `taxes` | [geno-taxes](https://github.com/42euge/geno-taxes) | Tax document parsing, CPA packet prep, filing checklists |
| `kaggle` | [geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, competition discussion scraping |
| `dev` | [geno-dev](https://github.com/42euge/geno-dev) | Developer utilities (planned) |

Install any of them:

```bash
geno-tools install media
geno-tools install research
```

## What a skillset provides

When you install a skillset, you get:

- **Slash commands** — markdown files that appear as `/gt-*` commands in your coding agent
- **SKILL.md** — an umbrella manifest describing the skillset's capabilities
- **Runtime scripts** (optional) — Python/shell scripts symlinked for command use
- **Config defaults** (optional) — copy-once configs that preserve user edits across updates
- **Isolated venvs** (optional) — Python dependencies that don't pollute your system

## External skillsets

You can install any repo that has a `genotools.yaml` at its root:

```bash
geno-tools install https://github.com/someone/geno-custom.git
geno-tools install ./my-local-skillset
```

See [Creating a Skillset](creating.md) for how to build your own.
