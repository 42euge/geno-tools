# geno-tools — meta-CLI for the geno-* ecosystem

`geno-tools` is the installer, manager, and compliance auditor for geno-* skillsets. It clones repos, sets up Python venvs, materializes bin symlinks, and registers skills with every supported coding agent in one command.

## Skills

| Skill | Category | Slash command |
|-------|----------|---------------|
| geno-tools | — | — (umbrella) |
| geno-tools-manager-status | manager | /geno-tools-manager-status |
| geno-tools-manager-discover | manager | /geno-tools-manager-discover |
| geno-tools-manager-install | manager | /geno-tools-manager-install |
| geno-tools-manager-remove | manager | /geno-tools-manager-remove |
| geno-tools-manager-upgrade | manager | /geno-tools-manager-upgrade |
| geno-tools-manager-update | manager | /geno-tools-manager-update |
| geno-tools-manager-deps | manager | /geno-tools-manager-deps |
| geno-tools-manager-doctor | manager | /geno-tools-manager-doctor |
| geno-tools-audit-run | audit | /geno-tools-audit-run |
| geno-tools-meta-harness-fork | meta/harness | /geno-tools-meta-harness-fork |
| geno-tools-meta-harness-use | meta/harness | /geno-tools-meta-harness-use |
| geno-tools-meta-harness-promote | meta/harness | /geno-tools-meta-harness-promote |
| geno-tools-meta-ecosystem-discover | meta/ecosystem | /geno-tools-meta-ecosystem-discover |
| geno-tools-meta-ecosystem-scan | meta/ecosystem | /geno-tools-meta-ecosystem-scan |
| geno-tools-meta-ecosystem-onboarding | meta/ecosystem | /geno-tools-meta-ecosystem-onboarding |
| geno-tools-author-skill | author | /geno-tools-author-skill |
| geno-tools-author-repo | author | /geno-tools-author-repo |
| geno-tools-setup | — | /geno-tools-setup |

## Repo structure

```
geno-tools/
├── GENO.md              # agent instructions (this file)
├── CLAUDE.md            # Claude Code pointer → @./GENO.md
├── AGENTS.md            # Codex/OpenCode pointer → @import GENO.md
├── SKILL.md             # umbrella skill manifest
├── SKILLS.md            # nesting standard documentation
├── genotools.yaml       # geno-tools manifest (name, version, description)
├── pyproject.toml       # Python package (geno_tools)
├── package.json         # Claude Code plugin manifest (skills array)
├── plugin.json          # Claude Code plugin entrypoint
├── gemini-extension.json # Gemini CLI extension manifest
├── geno_tools/          # Python CLI package
│   ├── __init__.py      #   version: __version__
│   ├── __main__.py      #   python -m geno_tools entrypoint
│   ├── cli.py           #   Click CLI root (geno-tools [cmd])
│   ├── commands.py      #   install, remove, upgrade, update, status, discover, deps
│   ├── audit.py         #   deterministic audit engine (FAIL/WARN/INFO checks)
│   ├── discovery.py     #   GitHub-driven registry discovery
│   ├── docs.py          #   SKILL.md-driven docs compilation
│   ├── registry.py      #   skillset registry (resolve name → URL)
│   ├── paths.py         #   ~/.geno/ path constants
│   ├── config.py        #   config.yaml reader
│   └── trace.py         #   geno-trace emit
├── skills/              # skill definitions (category tree)
│   ├── geno-tools/      #   umbrella
│   ├── manager/         #   install/remove/upgrade/update/status/discover/deps/doctor
│   ├── audit/run/       #   ecosystem compliance auditor
│   ├── meta/harness/    #   fork · use · promote
│   ├── meta/ecosystem/  #   discover · scan · onboarding
│   ├── author/          #   skill · repo scaffolding
│   └── setup/           #   one-time install
├── docs/                # MkDocs Material site
├── tests/               # pytest suite
└── .specs/              # GOALS.md, TENETS.md, VISION.md
```

## Conventions

### Command prefix aliasing

Skills in this repo always use the canonical `geno-` prefix (e.g. `/geno-tools-manager-install`). The prefix users type (`/gt-`, `/geno-`, or bare `/`) is configured per-installation in `~/.geno/config.yaml` and applied by `geno-tools install`. Never hardcode an aliased prefix like `/gt-` in any committed file.

### Versioning

The single source of version truth is `genotools.yaml`. The following files must all match it:

- `pyproject.toml` → `project.version`
- `geno_tools/__init__.py` → `__version__`
- `SKILL.md` frontmatter → `metadata.version`

Bump the version when adding or removing skills, or when changing behavior. Use semver: MAJOR.MINOR.PATCH.

### Agent instruction files

`CLAUDE.md` contains `@./GENO.md` and `AGENTS.md` contains `@import GENO.md` — both are thin pointers so every agent reads this file. After editing `GENO.md`, no copy step is needed: the pointers resolve at agent load time.

### Adding a new skill

1. Create `skills/<category>/<name>/SKILL.md` with frontmatter (`name`, `description`, `allowed-tools`, `license`, `metadata.version`).
2. The `name` must be the fully-qualified dotted-by-hyphen path: `geno-tools-<category>-<name>`.
3. Update the Skills table in this file.
4. Update the umbrella `SKILL.md` description to mention the new slash command.
5. Bump the version in `genotools.yaml`, `pyproject.toml`, `geno_tools/__init__.py`, and root `SKILL.md` metadata.
6. Add CLI subcommand in `geno_tools/commands.py` if the skill has a backing command.

### Single source of truth

Ecosystem-wide conventions (nomenclature, required files, SKILL.md format) are defined in the geno-tools audit spec (`skills/audit/run/SKILL.md`) and docs — not in this file. This GENO.md describes this repo; the audit skill describes the ecosystem.

## CLI

Entry point: `geno-tools = "geno_tools.cli:main"`

| Command | Description |
|---------|-------------|
| `geno-tools status` | Installed skillsets: version, commit, drift vs main |
| `geno-tools discover` | Installable skillsets, grouped by category |
| `geno-tools install <repo>` | Clone, venv, register with all agents |
| `geno-tools remove <repo>` | Uninstall from all agents |
| `geno-tools upgrade [repo]` | Pull latest + re-register |
| `geno-tools update` | Update geno-tools itself to latest version |
| `geno-tools deps <repo>` | Dependency tree |
| `geno-tools audit [path]` | Run ecosystem compliance audit |
| `geno-tools doctor` | Diagnose installation issues |

## Architecture

`geno-tools install` flow: resolve the repo name via `registry.py` → `git clone` into `~/.geno/geno-{name}/main/` → create venv if `genotools.yaml` has a `venv` section → materialize `runtime` bin symlinks → run `npx skills add` (or equivalent) to register skills with each agent.

The audit engine (`audit.py`) runs deterministic checks at three tiers — FAIL (blocks install), WARN (recommended), INFO (advisory) — and returns structured results that the `audit/run` skill then interprets and remediates.

## Dependencies and runtime

- **Python >= 3.10**
- **Node.js** for `npx skills add` (skill registration)
- **git** for clone/fetch operations
