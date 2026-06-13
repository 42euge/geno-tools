# Skillsets

A **skillset** is a self-contained repo that adds capabilities to an AI coding agent. Each skillset is a **layer**: a `layer.json` declaring its ecosystem category, plus skills under `skills/<category>/<name>/SKILL.md`. geno-tools compiles layers into agent environments.

## Ecosystem layers

These skillset repos are part of the geno ecosystem and can be added to any manifest as layers:

| Repo | Description |
|------|-------------|
| [geno-agents](https://github.com/42euge/geno-agents) | Agent coordination, registration, status updates, autonomous loops |
| [geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts, TTS/STT |
| [geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| [geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, competition discussion scraping |
| [geno-dev](https://github.com/42euge/geno-dev) | Developer utilities (planned) |

Use any of them by adding the repo to your `geno-image.yaml` and baking:

```yaml
layers:
  - https://github.com/42euge/geno-media

install:
  - core/geno-media
```

```bash
geno bake
```

The interactive builder (`geno`) can also discover these repos from GitHub and add them for you.

## What a skillset provides

When you bake a skillset's skills into your environment, you get:

- **Skills** — `SKILL.md` files that register as slash commands in your coding agent (the command prefix is [user-configurable](creating.md#command-prefix-aliasing))
- **GENO.md** — agent instructions, the single source of truth read by all supported coding agents
- **layer.json** — the ecosystem category the builder uses to group the layer
- **Audited content** — every skill passes the compliance scan before it enters a build

## External skillsets

Any repo with a `layer.json` and a `skills/` directory works as a layer:

```yaml
layers:
  - https://github.com/someone/geno-custom
  - ./my-local-skillset
```

See [Creating a Skillset](creating.md) for how to build your own.
