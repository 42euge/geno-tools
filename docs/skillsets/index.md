# Skillsets

A **skillset** is a self-contained repo that adds capabilities to an AI coding agent. Each skillset ships a `genotools.yaml` manifest declaring what to set up; geno-tools handles the rest.

## Registry

These skillsets are built into the geno-tools registry and can be installed by full repo name:

| Repo | Description |
|------|-------------|
| [geno-agents](https://github.com/42euge/geno-agents) | Agent coordination, registration, status updates, autonomous loops |
| [geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts, TTS/STT |
| [geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| [geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, competition discussion scraping |
| [geno-dev](https://github.com/42euge/geno-dev) | Developer utilities (planned) |

Install any of them:

```bash
geno-tools install geno-<name>
```

## What a skillset provides

When you install a skillset, you get:

- **Skills** — `SKILL.md` files under `skills/` that register as slash commands in your coding agent (the command prefix is [user-configurable](creating.md#command-prefix-aliasing))
- **SKILL.md** — an umbrella manifest describing the skillset's capabilities
- **GENO.md** — agent instructions, the single source of truth read by all supported coding agents
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
