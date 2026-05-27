# geno-tools — Agent-Agnostic Meta Package Manager for AI Coding Agents

`geno-tools` is an agent-agnostic meta package manager for AI coding agents. It discovers skills from open-source and private ecosystems, absorbs external skill systems (Vercel Labs Skills, Superpowers, Ralphy Loop plugins) into a unified framework, and manages their lifecycle across all supported agents (Claude Code, Gemini CLI, Codex, OpenCode, Cursor). A meta-harness layer evaluates and refines skill variations over time, while built-in auditing ensures capabilities evolve safely.

@./VISION.md
@./TENETS.md

## Skills

Skills are organized into 6 functional sub-skillsets under `skills/`. The full naming and layout convention is in [docs/skillsets/upstream-conventions.md](docs/skillsets/upstream-conventions.md).

| Skill | Sub-skillset | Slash command |
|-------|--------------|---------------|
| geno-tools | — | — (umbrella) |
| geno-lifecycle | lifecycle | — (sub-umbrella) |
| geno-lifecycle-repo-create | lifecycle | /geno-lifecycle-repo-create |
| geno-lifecycle-skill-create | lifecycle | /geno-lifecycle-skill-create |
| geno-lifecycle-install | lifecycle | /geno-lifecycle-install |
| geno-lifecycle-status | lifecycle | /geno-lifecycle-status |
| geno-compliance | compliance | — (sub-umbrella) |
| geno-compliance-audit | compliance | /geno-compliance-audit |
| geno-compliance-onboarding | compliance | /geno-compliance-onboarding |
| geno-self | self | — (sub-umbrella) |
| geno-self-update | self | /geno-self-update |
| geno-self-improve | self | /geno-self-improve |
| geno-self-session-spawn | self | /geno-self-session-spawn |
| geno-self-docs-open | self | /geno-self-docs-open |
| geno-workspaces | workspaces | — (sub-umbrella) |
| geno-workspaces-data-init | workspaces | /geno-workspaces-data-init |
| geno-assets | assets | — (sub-umbrella) |
| geno-assets-icons | assets | /geno-assets-icons |
| geno-config | config | — (sub-umbrella) |
| geno-config-alias | config | /geno-config-alias |

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
│   ├── registry.py                #   curated registry of known skillsets
│   └── trace.py                   #   skill trace system (emit/list/health)
├── skills/                        # skill definitions (nested tree per upstream conventions)
│   ├── geno-tools/SKILL.md        #   skillset-root umbrella mirror
│   ├── lifecycle/                 #   sub-skillset: skill & skillset CRUD
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── repo-create/       #     bootstrap a new geno-* repo (+ rules/)
│   │       ├── skill-create/
│   │       ├── install/
│   │       └── status/
│   ├── compliance/                #   sub-skillset: audit + onboarding gate
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── audit/             #     compliance auditor (+ rules/)
│   │       └── onboarding/
│   ├── self/                      #   sub-skillset: geno-tools self-mgmt
│   │   ├── SKILL.md
│   │   └── skills/
│   │       ├── update/
│   │       ├── improve/
│   │       ├── session-spawn/
│   │       └── docs-open/
│   ├── workspaces/                #   sub-skillset: data workspace scaffolding
│   │   ├── SKILL.md
│   │   └── skills/
│   │       └── data-init/
│   ├── assets/                    #   sub-skillset: generated branding
│   │   ├── SKILL.md
│   │   └── skills/
│   │       └── icons/
│   └── config/                    #   sub-skillset: user personalization
│       ├── SKILL.md
│       └── skills/
│           └── alias/
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
geno-trace = "genotools.trace:main"
```

`genotools/cli.py` parses subcommands and lazy-imports `genotools.commands` to keep `--version`/`--help` fast.

`genotools/trace.py` provides the `geno-trace` CLI for emitting and querying skill traces. Traces are append-only JSONL at `~/.geno/traces/YYYY/YYYY-MM.jsonl`. Health cards are aggregated per-skill at `~/.geno/health/<skill>.json`.

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
| `geno-tools discover [--dry-run]` | implemented |
| `geno-tools scan [--namespace] [--dry-run]` | implemented |
| `geno-tools docs [--docs-dir] [--dry-run]` | implemented |

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

### Versioning

The canonical version lives in `genotools.yaml` (`version` field). The same value must appear in `pyproject.toml` (`project.version`), `package.json` (`version`), and `genotools/__init__.py` (`__version__`). Bump the version whenever skills are added, removed, or behavior changes. Keep all four files in sync.

### Adding a new skill

This repo uses the nested skill tree layout — see [docs/skillsets/upstream-conventions.md § Nested skill trees](docs/skillsets/upstream-conventions.md#nested-skill-trees) for the rules.

1. Pick a sub-skillset for the new skill (`lifecycle`, `compliance`, `self`, `workspaces`, `assets`, `config`) or create a new one. Create a directory under `skills/{sub-skillset}/skills/{leaf}/` named with a bare noun/verb (no `geno-` prefix).
2. Write a `SKILL.md` inside the leaf directory. Frontmatter `name:` is the **fully qualified** name (e.g. `name: geno-self-foo`) — this is the registered skill name regardless of directory shape.
3. Update the parent sub-skillset's umbrella `SKILL.md` (`skills/{sub-skillset}/SKILL.md`) to list the new leaf.
4. Add a row to the skills table in this file.
5. If the skill needs docs, add a page under `docs/skills/geno-tools/{sub-skillset}/`.
6. Bump the version in all four files: `genotools.yaml`, `pyproject.toml`, `package.json`, `genotools/__init__.py`.

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

### Skill observability contract

Skills may declare an optional `observability` section in SKILL.md frontmatter:

```yaml
observability:
  success_signal: "description of what success looks like"
  failure_signals:
    - "condition that indicates failure"
  knowledge_reads:
    - "what knowledge this skill consumes"
  knowledge_writes:
    - "what knowledge this skill produces"
```

Skills that declare observability should also include a `## Completion` section at the end of their workflow that emits a trace via `geno-trace emit`. This feeds the self-improvement loop (health cards, retro, mining).

## Plugin structure

geno-tools ships platform-specific plugin manifests following the `obra/superpowers` conventions so it can be installed as a native plugin on each supported CLI. Skills are platform-agnostic; each CLI-specific manifest points at the shared `skills/` directory.

Skill registration uses `npx skills add <active-worktree> --agent '*' --global --skill '*' --yes`. Uninstall enumerates skills by walking the `skills/` tree at any depth (`genotools.commands._walk_skill_dirs`) and calls `npx skills remove` with the frontmatter `name:` of each registered skill.

This absorption layer is what makes geno-tools a meta-harness rather than just a CLI — external skill systems (Superpowers conventions, Vercel Labs Skills backend) are normalized into the same `SKILL.md` + `genotools.yaml` contract.
