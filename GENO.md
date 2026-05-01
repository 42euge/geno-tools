# geno-tools — Skillset Manager for the Geno Ecosystem

`geno-tools` is a meta-CLI and coding-agent plugin that installs sibling `geno-{name}` repos as coding agent skillsets. It handles cloning, venvs, bin symlinks, dependency resolution, and skill registration across all supported agents (Claude Code, Gemini CLI, Codex, OpenCode, Cursor).

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-tools | — | — (umbrella) |
| geno-audit | — | /geno-audit |
| geno-icons | — | /geno-icons |
| geno-onboarding | — | /geno-onboarding |
| geno-data-workspaces-init | — | /geno-data-workspaces-init |
| geno-tools-update | — | /geno-tools-update |
| geno-skills-create | — | /geno-skills-create |
| geno-tools-open-docs | — | /geno-tools-open-docs |

## Repo structure

```
geno-tools/
├── GENO.md                        # agent instructions (this file)
├── SKILL.md -> skills/geno-tools/SKILL.md  # umbrella skill manifest
├── genotools.yaml                 # geno-tools manifest
├── CLAUDE.md                      # Claude Code pointer -> GENO.md
├── GEMINI.md                      # Gemini CLI pointer -> GENO.md
├── AGENTS.md                      # Codex pointer -> GENO.md
├── gemini-extension.json          # Gemini CLI extension descriptor
├── package.json                   # npm metadata (OpenCode plugin entry)
├── pyproject.toml                 # Python package metadata
├── genotools/                     # Python CLI package
│   ├── cli.py                     #   argparse, subcommand routing
│   ├── commands.py                #   install/remove/update/ls/deps
│   ├── config.py                  #   user config from ~/.geno/config.yaml
│   ├── discovery.py               #   enterprise repo discovery
│   ├── paths.py                   #   on-disk layout utilities
│   └── registry.py                #   curated registry of known skillsets
├── skills/                        # skill definitions
│   ├── geno-tools/SKILL.md        #   umbrella skill
│   ├── geno-audit/SKILL.md        #   ecosystem compliance auditor
│   ├── geno-icons/SKILL.md        #   pixel art icon generator
│   ├── geno-onboarding/SKILL.md   #   skillset onboarding wizard
│   ├── geno-data-workspaces-init/SKILL.md  # data workspace scaffolder
│   ├── geno-skills-create/SKILL.md #  skill scaffolder
│   ├── geno-tools-update/SKILL.md #   ecosystem updater
│   └── geno-tools-open-docs/SKILL.md      # docs site opener
├── config/defaults.yaml           # reference config with aliases schema
├── scripts/bootstrap.sh           # self-installs geno-tools onto PATH
├── hooks/                         # Claude Code SessionStart hook
├── docs/                          # MkDocs Material documentation site
├── .claude-plugin/plugin.json     # Claude Code plugin manifest
├── .codex-plugin/plugin.json      # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json     # Cursor plugin manifest
├── .opencode/                     # OpenCode plugin
└── tests/                         # pytest suite
```

## Entry point

```toml
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
| `geno-tools update [name]` | implemented |
| `geno-tools deps <name>` | implemented |
| `geno-tools dev <name> <path>` | stub |
| `geno-tools fork <name> <variant> [--isolated-venv]` | stub |
| `geno-tools use <name>@<variant> [--here]` | stub |
| `geno-tools promote <name> <variant>` | stub |
| `geno-tools doctor` | stub |

## Dependency management

Skillsets declare dependencies via `requires:` in `genotools.yaml`:

```yaml
name: geno-career
requires:
  - geno-notes
  - geno-specs
```

During `geno-tools install`, dependencies are resolved from the registry and installed recursively before the target skillset. Already-installed deps are skipped. Circular dependencies are detected and reported.

## Source resolution

`<name|url|path>` resolves in this order:

1. **Registered repo name** — git URL from `genotools/registry.py`. Bare slugs (the part after `geno-`) are also accepted.
2. **Existing local directory** — installed from disk.
3. **Git URL** (`http(s)://`, `git@`, or `*.git`) — cloned.
4. **Discovery sources** (`genotools/discovery.py`) — repos found in `~/.geno/config.yaml` `discovery.sources` that match the configured prefix and have a top-level `SKILL.md`.

## Install flow

```
geno-tools install media
    ├── _resolve_source("media")         # registry -> git URL
    ├── _clone_and_worktree()            # bare clone + main worktree
    ├── _create_venv_if_needed()         # venv + pip install deps + editable install
    ├── _materialize_bin_symlinks()       # ~/.local/bin/ symlinks to venv binaries
    ├── active -> main symlink
    └── _install_skills_via_npx()        # npx skills add (all agents, global)
```

## Per-skillset layout

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

## Conventions

### Command prefix aliasing

Slash commands in this repo always use the canonical `geno-` prefix (e.g., `/geno-tools-update`, `/geno-audit`). The prefix users actually type at runtime (`/gt-`, `/geno-`, or bare `/`) is a user preference configured in `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"   # gt-install, gt-media-audiobook-create, etc.
```

The prefix is applied at install time by `geno-tools install` when materializing skills via `npx skills add`. Never hardcode an aliased prefix like `gt-` in SKILL.md descriptions, GENO.md, or any committed file. See `config/defaults.yaml` for the full schema.

### Adding a new skill

To add a new skill to this repo:

1. Create a directory under `skills/` named with the full skill name (e.g., `skills/geno-tools-foo/`).
2. Write a `SKILL.md` inside it with YAML frontmatter containing at minimum `name` and `description`.
3. Update the umbrella skill description in `skills/geno-tools/SKILL.md` to list the new skill.
4. Add the skill to the skills table in this file (`GENO.md`).
5. If the skill needs docs, add a page under `docs/`.

### What a skillset repo needs to provide

Minimum viable `geno-{name}` skillset:

```
geno-{name}/
├── SKILL.md                # umbrella skill manifest (symlink to skills/{name}/SKILL.md)
├── GENO.md                 # agent instructions
├── genotools.yaml          # install manifest (name, version, description)
├── skills/
│   └── {name}/SKILL.md     # umbrella skill definition
└── pyproject.toml           # optional — triggers venv creation if present
```

## Plugin structure

geno-tools ships platform-specific plugin manifests following the `obra/superpowers` conventions so it can be installed as a native plugin on each supported CLI. Skills are platform-agnostic; each CLI-specific manifest points at the shared `skills/` directory.

Skill registration uses `npx skills add <active-worktree> --agent '*' --global --skill '*' --yes`. Uninstall enumerates skills (root SKILL.md + `skills/*/SKILL.md`) and calls `npx skills remove`.
