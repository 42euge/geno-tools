# geno-tools

Meta-CLI for installing and managing [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skillsets in the `geno-*` ecosystem.

## What it does

`geno-tools` installs/uninstalls/dev-links curated skillset repos (each a `geno-{name}` repo with its own `genotools.yaml` manifest) into agent targets — Claude Code first, Codex and Gemini CLI to follow. Inspired by [vercel-labs/skills](https://github.com/vercel-labs/skills), specialized for this ecosystem:

- **Curated registry** — short names (`media`, `research`, `taxes`, …) resolve to git URLs
- **Declarative install** — each skillset's `genotools.yaml` declares its venv deps, runtime symlinks, and config defaults
- **Per-skillset venvs** — isolated at `~/.geno-tools/geno-{name}/venvs/`
- **Copy-once configs** — user edits preserved across updates
- **Dev-link** — point at a local checkout for meta-improvement

## Install

```bash
pipx install git+https://github.com/42euge/geno-tools
```

## Usage

```bash
geno-tools ls --available                # registry
geno-tools install media                 # install geno-media
geno-tools dev media ~/src/geno-media    # link a local dev checkout
geno-tools ls                            # installed
geno-tools doctor                        # verify links, venvs, targets
geno-tools update media
geno-tools remove media [--keep-data]
```

## Layout

```
~/.geno-tools/
└── geno-{name}/
    ├── repo/       # cloned source (or symlink to dev checkout)
    ├── venvs/      # per-skillset Python environments
    ├── scripts/    # symlinks into repo/runtime/
    └── configs/    # copy-once user-editable configs
```

## Skillsets

| Name | Repo | Status |
|---|---|---|
| `media` | [42euge/geno-media](https://github.com/42euge/geno-media) | ✅ extracted |
| `research` | [42euge/geno-research](https://github.com/42euge/geno-research) | ✅ extracted |
| `taxes` | `42euge/geno-taxes` | 🚧 pending |
| `kaggle` | `42euge/geno-kaggle` | 🚧 pending |
| `dev` | `42euge/geno-dev` | 🚧 pending |

## Legacy (transitional)

Some slash commands still live in this repo's `commands/` — `gt-start-task`, `gt-rewrite-commit`, `gt-config-colab`, `gt-upload-colab`, `gt-upload-kaggle`. These will migrate into `geno-dev` and `geno-kaggle` as those repos come online.

A legacy `install.sh` is still present to wire up the remaining commands and colab config. It will be removed once everything is extracted.

## License

MIT
