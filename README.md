# geno-tools

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/geno-tools/)

Skills-only repo that distributes the `geno-tools` skillset catalog. This package is no longer a Python CLI.

**Website:** <https://42euge.github.io/geno-tools>

## What it does

`geno-tools` is a pure-skill collection with:

- **Installable skills** in `skills/`
- **Agent plugin descriptors** for Claude Code, Codex, Cursor, OpenCode, and Antigravity CLI
- **Documentation** and skill metadata

## Install into an agent

Install this repo as a plugin/skillset in your agent of choice:

### Claude Code

```bash
/plugin marketplace add 42euge/geno-tools
/plugin install geno-tools@geno-tools
```

### Antigravity CLI

```bash
agy plugin install https://github.com/42euge/geno-tools
```

### Codex CLI

```bash
/plugin marketplace add 42euge/geno-tools
/plugins
```

### Cursor

Install via Cursor's plugin manager (it reads `.cursor-plugin/plugin.json`) or clone the repo into your Cursor plugins directory.

### OpenCode

Add this to `opencode.json`:

```json
{ "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"] }
```

## Available skillset surface

The `geno-tools` umbrella skill exposes:

- `/geno-tools` — skillset overview
- `/geno-tools-update` — refresh installed skillsets via existing host tooling
- `/geno-skills-install` — register a local skillset checkout globally
- `/geno-skills-create` — scaffold a new skill
- `/geno-audit` — check a repo against ecosystem conventions
- plus additional companion `geno-*` skills in this repo

## Project structure

```
.
├── GENO.md                    # agent-facing canonical guidance
├── skills/                    # SKILL.md definitions
├── docs/                      # MkDocs Material docs
├── docs-home.md               # docs landing
├── genotools.yaml             # skillset manifest
├── .claude-plugin/            # Claude Code manifest
├── .codex-plugin/             # Codex manifest
├── .cursor-plugin/            # Cursor manifest
├── .opencode/                 # OpenCode plugin entry
├── plugin.json                # Antigravity plugin manifest
└── GEMINI.md, AGENTS.md, CLAUDE.md
```

## Notes

- No `pyproject.toml`
- No `genotools/` Python package
- No bootstrap or installer scripts

## External skillset management

If you need the Python package for local CLI orchestration (`geno-tools install`, `geno-tools ls`, etc.), that flow is now out of scope for this repo.

## License

MIT
