# geno-tools — skillset manager for the geno ecosystem

`geno-tools` is a meta-CLI and Claude Code plugin (Python, `pipx install geno-tools`) that installs sibling `geno-{name}` repos as coding agent skillsets. It handles cloning, venvs, bin symlinks, and skill registration via `npx skills`.

## Dual installation

- **Claude Code plugin**: `.claude-plugin/plugin.json` + `skills/` expose the geno-tools skill
- **Python CLI**: `pyproject.toml` → `geno-tools` binary on PATH via pipx/pip

The plugin wraps the CLI — both require the Python package installed.

## Entry point

```toml
# pyproject.toml
[project.scripts]
geno-tools = "genotools.cli:main"
```

`genotools/cli.py` parses subcommands and lazy-imports `genotools.commands` to keep `--version`/`--help` fast.

## Subcommands

| Command | Status |
|---------|--------|
| `geno-tools ls [--available]` | implemented |
| `geno-tools install <name\|url\|path> [--here]` | implemented |
| `geno-tools remove <name> [--keep-data]` | implemented |
| `geno-tools update [name]` | stub |
| `geno-tools dev <name> <path>` | stub |
| `geno-tools fork <name> <variant> [--isolated-venv]` | stub |
| `geno-tools use <name>@<variant> [--here]` | stub |
| `geno-tools promote <name> <variant>` | stub |
| `geno-tools doctor` | stub |

## Command prefix aliasing

The `gt-` prefix on slash commands (e.g., `/gt-install`) is a **user preference**, not baked into skillset repos. It's configured in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # gt-install, gt-media-audiobook-create, etc.
```

See `config/defaults.yaml` for the full schema. The prefix is read at install time by `genotools/config.py` and applied when materializing slash commands.

## Source resolution (`commands._resolve_source`)

`<name|url|path>` resolves in this order:

1. **Registered repo name** → git URL from `genotools/registry.py` (currently `geno-agents`, `geno-media`, `geno-research`, `geno-kaggle`, `geno-dev`). Bare slugs like `media` are accepted as a backwards-compat fallback.
2. **Existing local directory** → installed from disk.
3. **Git URL** (`http(s)://`, `git@`, or `*.git`) → cloned.
4. **Discovery sources** (`genotools/discovery.py`) → repos found in `~/.geno/config.yaml` `discovery.sources` (GitHub Enterprise, GitLab, etc.) that match the configured prefix and have a top-level `SKILL.md`.

For URLs and paths the skillset name isn't known upfront. A shallow clone to `~/.geno-tools/.staging/` reads `pyproject.toml` for the project name, then the full install proceeds.

## Install flow

```
geno-tools install media
    ├── _resolve_source("media")         # registry → git URL
    ├── _clone_and_worktree()            # bare clone + main worktree
    ├── _create_venv_if_needed()         # venv + pip install deps + editable install
    ├── _materialize_bin_symlinks()       # ~/.local/bin/ symlinks to venv binaries
    ├── active -> main symlink
    └── _install_skills_via_npx()        # npx skills add (all agents, global)
```

On failure at any step, the partially created directory is cleaned up.

## Per-skillset layout

`genotools/paths.py` defines everything under `~/.geno-tools/`:

```
~/.geno-tools/
├── .state-hash                    # bumped on state changes
├── geno-bootstrap/                # meta-plugin geno-tools owns
└── geno-{name}/
    ├── .git/                      # bare repo
    ├── main/                      # primary worktree
    ├── .worktrees/<variant>/      # additional worktrees (via fork)
    ├── venvs/<venv-name>/         # isolated Python env(s)
    └── active -> main             # symlink; `geno-tools use` repoints this
```

## Skill registration

`npx skills add <active-worktree> --agent '*' --global --skill '*' --yes` registers SKILL.md with all supported agents (Claude Code, Codex, Cursor, Gemini CLI, etc.).

Uninstall enumerates skills (root SKILL.md + `skills/*/SKILL.md`) and calls `npx skills remove`.

## Plugin structure (this repo)

geno-tools ships platform-specific plugin manifests following the `obra/superpowers` conventions so it can be installed as a native plugin on each supported CLI:

```
geno-tools/
├── .claude-plugin/plugin.json   # Claude Code plugin manifest
├── .codex-plugin/plugin.json    # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json   # Cursor plugin manifest
├── .opencode/                   # OpenCode plugin
│   ├── plugins/geno-tools.js    #   ES module plugin (registers skills path)
│   └── INSTALL.md               #   installation instructions
├── gemini-extension.json        # Gemini CLI extension descriptor
├── GEMINI.md                    # Gemini CLI bootstrap context (@-imports SKILL.md)
├── package.json                 # npm metadata (entry point for OpenCode plugin)
├── skills/geno-tools/SKILL.md   # umbrella skill describing the meta-CLI
├── config/defaults.yaml         # reference config with aliases schema
├── genotools/                   # Python CLI package
│   ├── cli.py                   # argparse, subcommand routing
│   ├── commands.py              # install/remove implemented, rest are stubs
│   ├── config.py                # user config from ~/.geno/config.yaml
│   ├── paths.py                 # on-disk layout utilities
│   └── registry.py              # curated registry of known skillsets
└── pyproject.toml               # pip/pipx entry point
```

Skills are platform-agnostic. Each CLI-specific manifest points at the shared `skills/` directory.

## What a skillset repo needs to provide

Minimum viable `geno-{name}` skillset:

```
geno-{name}/
├── SKILL.md                # umbrella skill manifest
├── commands/
│   └── {name}-*.md         # slash commands (any *.md works)
└── pyproject.toml           # optional — triggers venv creation if present
```

Skillsets use the skills format (not the plugin format). Only geno-tools itself ships as a Claude Code plugin.
