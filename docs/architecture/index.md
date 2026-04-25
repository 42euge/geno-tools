# Architecture

geno-tools is structured around a few core concepts:

## Dual installation

geno-tools itself can be installed two ways:

- **Claude Code plugin** — `claude /plugin install 42euge/geno-tools` adds slash commands (`/geno-tools-install`, `/geno-tools-ls`, etc.) inside Claude Code
- **Python CLI** — `pipx install git+https://github.com/42euge/geno-tools` puts the `geno-tools` binary on your PATH

The plugin wraps the CLI, so both paths require the Python package. The ecosystem skillsets geno-tools installs remain skills-based (registered via `npx skills add`).

## Source resolution

When you run `geno-tools install <name|url|path>`, the source is resolved in order:

1. **Registered short name** — looked up in `genotools/registry.py`
2. **Local directory** — installed from disk
3. **Git URL** — cloned

For URLs and local paths, the skillset name isn't known upfront. geno-tools does a shallow clone to a staging directory, reads `pyproject.toml` for the project name, then proceeds with the full install.

## Install flow

```
geno-tools install media
        │
        ├── resolve source (registry → git URL)
        ├── bare clone into ~/.geno-tools/geno-media/.git/
        ├── create main worktree
        ├── create venv + editable install (if pyproject.toml exists)
        ├── symlink [project.scripts] binaries into ~/.local/bin/
        ├── set active -> main symlink
        └── npx skills add (register skills with Claude Code)
```

On failure at any step, the partially created `~/.geno-tools/geno-{name}/` directory is cleaned up automatically.

## Uninstall

Removal reverses the install:

1. `npx skills remove` — unregister skills from Claude Code
2. Remove `~/.local/bin/` symlinks that point into this skillset's venv
3. Delete `~/.geno-tools/geno-{name}/` (or preserve venvs/worktrees with `--keep-data`)

## Plugin structure

The geno-tools repo ships both a Python package and a Claude Code plugin:

```
geno-tools/
├── .claude-plugin/plugin.json   # Claude Code plugin manifest
├── skills/geno-tools/SKILL.md   # umbrella skill describing the meta-CLI
├── commands/                    # slash commands wrapping the CLI
│   ├── geno-tools-install.md
│   ├── geno-tools-remove.md
│   ├── geno-tools-ls.md
│   └── geno-tools-update.md
├── genotools/                   # Python CLI package
│   ├── cli.py
│   ├── commands.py
│   ├── paths.py
│   └── registry.py
└── pyproject.toml               # pip/pipx entry point
```

## Pages

- [Disk Layout](layout.md) — where everything lives on disk
- [Variants & Worktrees](variants.md) — the `fork`/`use`/`promote` workflow
