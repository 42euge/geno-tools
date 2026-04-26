# geno-tools

Meta-CLI for installing and managing coding agent skillsets in the `geno-*` ecosystem. Works with Claude Code, Codex, Gemini CLI, Cursor, and OpenCode.

## What it does

`geno-tools` installs/uninstalls/dev-links curated skillset repos (each a `geno-{name}` repo) into any supported coding agent. Inspired by [vercel-labs/skills](https://github.com/vercel-labs/skills) and [obra/superpowers](https://github.com/obra/superpowers), specialized for this ecosystem:

- **Curated registry** — short names (`media`, `research`, `taxes`, …) resolve to git URLs
- **Multi-agent** — skills register with all agents via `npx skills add --agent '*'`
- **Per-skillset venvs** — isolated at `~/.geno-tools/geno-{name}/venvs/`
- **Dev-link** — point at a local checkout for meta-improvement

## Install

### Python CLI (required for all platforms)

```bash
pipx install git+https://github.com/42euge/geno-tools
```

### Claude Code

```bash
claude /plugin install 42euge/geno-tools
```

### Codex CLI

Clone and symlink skills into `~/.agents/skills/geno-tools`, then install the Python CLI above.

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
```

### Cursor

Install via plugin manager or clone to your Cursor plugins directory.

### OpenCode

Add to `opencode.json`:
```json
{ "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"] }
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

Some slash commands still live in this repo's `commands/` — `gt-start-task`, `gt-rewrite-commit`, `gt-config-colab`, `gt-upload-colab`, `gt-upload-kaggle`. These will migrate into `geno-dev` and `geno-kaggle` as those repos come online. Lab notes have moved to the [`geno-notes`](https://github.com/42euge/geno-notes) repo (use `/gt-notes`).

A legacy `install.sh` is still present to wire up the remaining commands and colab config. It will be removed once everything is extracted.

## License

MIT
