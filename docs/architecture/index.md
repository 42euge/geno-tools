# Architecture

geno-tools is structured around a few core concepts:

## Multi-agent installation

geno-tools can be installed as a native plugin on any supported coding CLI:

- **Claude Code** — `claude /plugin install 42euge/geno-tools`
- **Codex CLI** — clone + symlink to `~/.agents/skills/geno-tools`
- **Cursor** — install via plugin manager
- **Gemini CLI** — `gemini extensions install https://github.com/42euge/geno-tools`
- **OpenCode** — add `"geno-tools@git+https://github.com/42euge/geno-tools.git"` to `opencode.json` plugins
- **Python CLI** — `pipx install git+https://github.com/42euge/geno-tools` puts the `geno-tools` binary on your PATH

All plugin paths wrap the Python CLI, so they require the Python package installed. The ecosystem skillsets geno-tools installs are registered with all agents via `npx skills add --agent '*'`.

## Source resolution

When you run `geno-tools install <name|url|path>`, the source is resolved in order:

1. **Registered repo name** — looked up in `genotools/registry.py`
2. **Local directory** — installed from disk
3. **Git URL** — cloned
4. **Discovery sources** — repos found in configured GitHub / GitLab / etc. groups (see `genotools/discovery.py`)

For URLs and local paths, the skillset name isn't known upfront. geno-tools does a shallow clone to a staging directory, reads `pyproject.toml` for the project name, then proceeds with the full install.

## Install flow

```
geno-tools install geno-<name>
        │
        ├── resolve source (registry → git URL)
        ├── bare clone into ~/.geno-tools/geno-<name>/.git/
        ├── create main worktree
        ├── create venv + editable install (if pyproject.toml exists)
        ├── symlink [project.scripts] binaries into ~/.local/bin/
        ├── set active -> main symlink
        └── npx skills add --agent '*' (register skills with all agents)
```

On failure at any step, the partially created `~/.geno-tools/geno-<name>/` directory is cleaned up automatically.

## Uninstall

Removal reverses the install:

1. `npx skills remove` — unregister skills from all agents
2. Remove `~/.local/bin/` symlinks that point into this skillset's venv
3. Delete `~/.geno-tools/geno-<name>/` (or preserve venvs/worktrees with `--keep-data`)

## Plugin structure

The geno-tools repo ships platform-specific plugin manifests (following `obra/superpowers` conventions) alongside the Python CLI:

```
geno-tools/
├── .claude-plugin/plugin.json   # Claude Code plugin manifest
├── .codex-plugin/plugin.json    # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json   # Cursor plugin manifest
├── .opencode/                   # OpenCode plugin
│   ├── plugins/geno-tools.js    #   ES module (registers skills path)
│   └── INSTALL.md
├── gemini-extension.json        # Gemini CLI extension descriptor
├── GEMINI.md                    # Gemini CLI bootstrap context
├── package.json                 # npm metadata (OpenCode entry point)
├── skills/geno-tools/SKILL.md   # umbrella skill (platform-agnostic)
├── commands/                    # slash commands (platform-agnostic)
│   ├── gt-install.md
│   ├── gt-remove.md
│   ├── gt-ls.md
│   └── gt-update.md
├── genotools/                   # Python CLI package
│   ├── cli.py
│   ├── commands.py
│   ├── paths.py
│   └── registry.py
└── pyproject.toml               # pip/pipx entry point
```

Skills and commands are shared across all platforms. Each CLI has its own manifest that points at these shared directories.

## Pages

- [Disk Layout](layout.md) — where everything lives on disk
- [Variants & Worktrees](variants.md) — the `fork`/`use`/`promote` workflow
