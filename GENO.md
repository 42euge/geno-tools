# geno-tools — Agent-Agnostic Skillset Manager

Meta-CLI for installing, updating, and managing geno-* skillsets across all supported coding agents (Claude Code, Antigravity CLI, Codex, OpenCode).

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-tools | — | — (umbrella) |
| geno-tools-setup | setup | /geno-tools-setup |
| geno-tools-manager-status | manager | /geno-tools-manager-status |
| geno-tools-manager-discover | manager | /geno-tools-manager-discover |
| geno-tools-manager-install | manager | /geno-tools-manager-install |
| geno-tools-manager-remove | manager | /geno-tools-manager-remove |
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
| geno-tools-tt | tt | /geno-tools-tt |

## Repo structure

```
geno-tools/
├── GENO.md                        # agent instructions (this file)
├── SKILL.md                       # umbrella skill manifest (root copy)
├── SKILLS.md                      # skill nesting standard reference
├── CLAUDE.md                      # → @./GENO.md
├── AGENTS.md                      # → @import GENO.md
├── GEMINI.md                      # → @./GENO.md
├── genotools.yaml                 # geno-tools manifest (version, deps)
├── pyproject.toml                 # Python package (geno-tools CLI)
├── geno_tools/                    # Python package
│   ├── cli.py                     # entry point — subcommands dispatcher
│   ├── commands.py                # install, remove, update, status, discover, deps
│   ├── registry.py                # skillset discovery (GitHub API, layer.json)
│   ├── trace.py                   # geno-trace CLI
│   ├── docs.py                    # geno-docs CLI
│   └── tt/                        # vendored terminal-tools (geno-tools tt)
├── skills/                        # skill definitions
│   ├── geno-tools/SKILL.md        #   umbrella
│   ├── setup/SKILL.md             #   /geno-tools-setup — bootstrap install
│   ├── tt/SKILL.md                #   /geno-tools-tt — terminal tools
│   ├── manager/                   #   status · discover · install · remove · update · deps · doctor
│   ├── audit/run/SKILL.md         #   /geno-tools-audit-run — compliance auditor
│   ├── meta/                      #   harness/ (fork · use · promote) + ecosystem/ (discover · scan · onboarding)
│   └── author/                    #   skill · repo — scaffold new skills/repos
├── docs/                          # MkDocs Material site
└── tests/                         # pytest suite
```

## Conventions

### Nomenclature

Skills in this repo follow the pattern `geno-tools-{sub-skillset}-{skill}`. Sub-skillset is a noun category (`manager`, `author`, `audit`), and skill is an action verb (`install`, `fork`, `run`). Deeper nesting uses hyphens: `geno-tools-meta-harness-fork`. The umbrella skill is just `geno-tools`.

### Adding a new skill

1. Create `skills/{category}/{name}/SKILL.md` with required frontmatter (`name`, `description`, `allowed-tools`, `license`, `metadata.author`, `metadata.version`).
2. Set `name` to the fully-qualified hyphen-joined path: `geno-tools-{category}-{name}`.
3. Update the umbrella descriptions in root `SKILL.md` and `skills/geno-tools/SKILL.md`.
4. Update this file's Skills table above.
5. Bump the version in `genotools.yaml`, `pyproject.toml`, `package.json`, `geno_tools/__init__.py`, root `SKILL.md`, and `skills/geno-tools/SKILL.md`.

### Command prefix aliasing

Slash command references in committed files (`SKILL.md`, this file, `README.md`, `docs/`) must always use the canonical `geno-` prefix (e.g. `/geno-tools-manager-install`). The prefix users actually type (`/gt-`, `/geno-`, or bare `/`) is set in `~/.geno/config.yaml` and applied by `geno-tools install`. Never hardcode an aliased prefix in any committed file.

### Versioning

The canonical version lives in `genotools.yaml`. Keep these files in sync: `genotools.yaml`, `pyproject.toml`, `package.json`, `geno_tools/__init__.py`, root `SKILL.md`, and `skills/geno-tools/SKILL.md`. Bump the version when adding or removing skills, changing CLI behavior, or shipping significant instruction updates.

## Architecture

`geno-tools` is a Python CLI package (`geno_tools`). Entry point: `geno_tools.cli:main`.

### CLI subcommands

| Subcommand | What it does |
|------------|-------------|
| `status` / `ls` | Installed skillsets with version, variant@commit, drift vs remote |
| `discover` / `ls --available` | Registry of installable skillsets, grouped by category |
| `install` | Clone repo, create venv, register skills with all agents |
| `remove` | Uninstall skillset from all agents |
| `update` | Pull latest main + re-register skills |
| `deps` | Dependency tree for a skillset |
| `tt` | Vendored terminal-tools subcommand |
| `geno-trace` | Emit skill execution telemetry |
| `geno-docs` | Serve or build the MkDocs documentation site |

### Key paths

- Skillsets install to `~/.geno/geno-{name}/main/` (bare clone + active worktree).
- Registry cache: `~/.geno/registry.json`.
- Skill registration: `npx skills add --full-depth` (vercel-labs/skills).

## Dependencies and runtime

- Python ≥ 3.11
- `pyyaml >= 6.0` (manifest parsing)
- Optional: `textual >= 0.40` (for `geno-tools tt tui`)
- Node.js with `npx` (for skill registration via `npx skills add`)
