# geno-tools — skillset manager for the geno ecosystem

`geno-tools` is a meta-CLI and Claude Code plugin (Python, `pipx install geno-tools`) that installs sibling `geno-{name}` repos as coding agent skillsets. It handles cloning, venvs, bin symlinks, and skill registration via `npx skills`.

## Dual installation

- **Claude Code plugin**: `.claude-plugin/plugin.json` + `skills/` + `commands/` expose `/geno-tools-install`, `/geno-tools-remove`, `/geno-tools-ls`, `/geno-tools-update` slash commands
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

| Command | Slash command | Status |
|---------|---------------|--------|
| `geno-tools ls [--available]` | `/geno-tools-ls` | implemented |
| `geno-tools install <name\|url\|path> [--here]` | `/geno-tools-install` | implemented |
| `geno-tools remove <name> [--keep-data]` | `/geno-tools-remove` | implemented |
| `geno-tools update [name]` | `/geno-tools-update` | stub |
| `geno-tools dev <name> <path>` | — | stub |
| `geno-tools fork <name> <variant> [--isolated-venv]` | — | stub |
| `geno-tools use <name>@<variant> [--here]` | — | stub |
| `geno-tools promote <name> <variant>` | — | stub |
| `geno-tools doctor` | — | stub |

## Source resolution (`commands._resolve_source`)

`<name|url|path>` resolves in this order:

1. **Registered short name** → git URL from `genotools/registry.py` (currently `agents`, `media`, `research`, `taxes`, `kaggle`, `dev`).
2. **Existing local directory** → installed from disk.
3. **Git URL** (`http(s)://`, `git@`, or `*.git`) → cloned.

For URLs and paths the skillset name isn't known upfront. A shallow clone to `~/.geno-tools/.staging/` reads `pyproject.toml` for the project name, then the full install proceeds.

## Install flow

```
geno-tools install media
    ├── _resolve_source("media")         # registry → git URL
    ├── _clone_and_worktree()            # bare clone + main worktree
    ├── _create_venv_if_needed()         # venv + pip install deps + editable install
    ├── _materialize_bin_symlinks()       # ~/.local/bin/ symlinks to venv binaries
    ├── active -> main symlink
    └── _install_skills_via_npx()        # npx skills add (claude-code, global)
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

`npx skills add <active-worktree> --agent claude-code --global --skill '*' --yes` fans SKILL.md and commands into `~/.claude/skills/` and `~/.claude/commands/`.

Uninstall enumerates skills (root SKILL.md + `skills/*/SKILL.md`) and calls `npx skills remove`.

## Nomenclature

Skills follow a strict naming hierarchy: `{skillset}-{sub-skillset}-{skill-slug}`.

- **Skillset** = a geno-ecosystem repo (e.g., `geno-tools`, `geno-kaggle`)
- **Sub-skillset** = pluralized noun grouping, ALWAYS required (e.g., `repos`, `icons`, `tasks`)
- **Skill slug** = action verb (e.g., `scaffold`, `generate`, `start`)
- **Umbrella skill** = just the skillset name (e.g., `geno-tools`)

See `docs/skillsets/nomenclature.md` for the full spec and cross-ecosystem migration reference.

## Plugin structure (this repo)

```
geno-tools/
├── .claude-plugin/plugin.json               # Claude Code plugin manifest
├── skills/geno-tools/SKILL.md               # umbrella skill
├── skills/geno-tools-repos-scaffold/SKILL.md  # repo scaffolding skill
├── skills/geno-tools-icons-generate/SKILL.md  # icon generation skill
├── commands/                                # slash commands wrapping the CLI
│   ├── geno-tools-install.md
│   ├── geno-tools-remove.md
│   ├── geno-tools-ls.md
│   ├── geno-tools-update.md
│   └── geno-tools-repos-scaffold.md
├── genotools/                               # Python CLI package
│   ├── cli.py                               # argparse, subcommand routing
│   ├── commands.py                          # install/remove implemented, rest are stubs
│   ├── paths.py                             # on-disk layout utilities
│   └── registry.py                          # curated registry of known skillsets
└── pyproject.toml                           # pip/pipx entry point
```

## What a skillset repo needs to provide

Every geno-ecosystem repo must have:

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions for agents, including compliance rules |
| `package.json` | Skills manifest with name, version, skills map |
| `.geno-agents` | Agent identity: role, description, capabilities |
| `skills/geno-{name}/SKILL.md` | Umbrella skill with YAML frontmatter |
| `README.md` | Human-facing docs: install, commands table, repo tree |

Minimum file structure:

```
geno-{name}/
├── CLAUDE.md               # compliance rules + project context
├── SKILL.md                # umbrella skill manifest
├── skills/
│   └── geno-{name}-{sub-skillset}-{skill}/
│       └── SKILL.md        # sub-skill (follows nomenclature)
├── commands/
│   └── geno-{name}-*.md    # slash commands (any *.md works)
└── pyproject.toml           # optional — triggers venv creation if present
```

Skillsets use the skills format (not the plugin format). Only geno-tools itself ships as a Claude Code plugin.

### CLAUDE.md compliance section

Every repo's CLAUDE.md must include a Compliance section covering:

1. **Nomenclature** — skill naming rules with repo-specific examples
2. **Repo structure** — required files table
3. **SKILL.md frontmatter** — template showing required fields
4. **Adding a new skill** — checklist of files to update

See `geno-dev/CLAUDE.md` as the reference implementation.
