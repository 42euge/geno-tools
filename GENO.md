# geno-tools

Unified geno control plane: **resolve · scope · launch**. geno-tools resolves
skillset bundles — skills at pinned variants, transitive `requires:` deps, and
MCP catalog names → server specs — and launches them in isolated containers
scoped to a **profile**. Raw skill *registration* is delegated to `npx skills`;
geno-tools owns everything `npx skills` can't do: dependency resolution,
variant pinning, MCP catalogs, per-invocation isolation, and the container
runtime (folded in from the former geno-iso repo).

Three layers:
- **`npx skills`** (external) — per-agent skill registration.
- **geno-tools** — resolve (skills@variant, deps, MCP catalogs), variant
  worktrees (fork/use/promote), profiles, and the MCP catalog adapter.
- **geno-iso** (`geno_tools/iso/`, `geno-iso` binary) — per-invocation
  isolated container launch.

A **profile** (`~/.geno/profiles/*.yaml`) is a named bundle of *(skills @
variant)* + *(MCP servers)* + target agents. `geno-tools launch <agent>
--profile <name>` materializes exactly that into one scoped container session.

## Skills table

| Skill | Sub-skillset / Category | Slash command |
|-------|------------------------|---------------|
| geno-tools | — | /geno-tools (umbrella) |
| geno-tools-setup | — | /geno-tools-setup |
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
| geno-tools-iso-containers-run | iso | /geno-tools-iso-containers-run |
| geno-tools-iso-containers-list | iso | /geno-tools-iso-containers-list |
| geno-tools-iso-containers-enter | iso | /geno-tools-iso-containers-enter |
| geno-tools-iso-images-build | iso | /geno-tools-iso-images-build |
| geno-tools-iso-credentials-extract | iso | /geno-tools-iso-credentials-extract |
| geno-tools-iso-housekeep | iso | /geno-tools-iso-housekeep |
| geno-tools-iso-dev-guide | iso | /geno-tools-iso-dev-guide |

## Profiles & launch (CLI, not skills)

- `geno-tools profile list|show <name>|create <name>` — manage `~/.geno/profiles/*.yaml`
- `geno-tools resolve <name>` — emit a profile's resolved plan as JSON (inspection seam)
- `geno-tools launch <agent> --profile <name> [workspace] [--rm]` — run a CLI in a
  geno-iso container scoped to the profile (skills at pinned variants bind-mounted,
  MCP servers injected). Hard-requires the `geno-iso` runtime.
- `geno-tools fork <name> <variant>` / `use <name>@<variant>` / `promote <name> <variant>` —
  variant worktree lifecycle that profiles pin against.
- `geno-iso …` — the container runtime binary (run/it/ls/stop/rm/build/creds).

## Repo structure

```
geno-tools/
├── GENO.md                    # agent instructions (this file)
├── CLAUDE.md                  # @./GENO.md pointer
├── AGENTS.md                  # @import GENO.md pointer
├── SKILL.md                   # umbrella skill manifest (root-level convenience copy)
├── SKILLS.md                  # skill nesting standard reference doc
├── genotools.yaml             # geno-tools manifest (name, version, description)
├── pyproject.toml             # Python package definition
├── package.json               # JS metadata (version parity with genotools.yaml)
├── plugin.json                # cross-agent plugin manifest
├── gemini-extension.json      # Gemini CLI extension descriptor
├── mkdocs.yml                 # documentation site config
├── skills/                    # skill definitions (nested category tree)
│   ├── geno-tools/SKILL.md    #   umbrella skill
│   ├── setup/SKILL.md         #   bootstrap / PATH setup
│   ├── manager/               #   install, remove, upgrade, update, status, discover, deps, doctor
│   ├── audit/                 #   ecosystem compliance auditor
│   ├── meta/harness/          #   fork / use / promote variant loop
│   ├── meta/ecosystem/        #   discover / scan / onboarding
│   ├── author/                #   scaffold skill and repo
│   └── iso/                   #   container run/list/enter, image build, creds, housekeep (folded from geno-iso)
├── geno_tools/                # Python package (CLI implementation)
│   ├── cli.py                 #   argparse entry point
│   ├── commands.py            #   subcommand dispatch (incl. fork/use/promote, profile, resolve, launch)
│   ├── profiles.py            #   profile store + resolver (~/.geno/profiles/*.yaml)
│   ├── mcp.py                 #   MCP catalog adapter (pluggable providers; write .mcp.json)
│   ├── registry.py            #   skillset registry lookup
│   ├── discovery.py           #   GitHub org scanning
│   ├── paths.py               #   ~/.geno/ path helpers (ROOT, PROFILES_DIR, ISO_DIR)
│   ├── config.py              #   config loading
│   ├── trace.py               #   geno-trace CLI
│   ├── docs.py                #   geno-docs CLI
│   ├── iso/                   #   geno-iso container runtime (cli, docker, profiles, credentials, dockerfiles/)
│   └── scripts/               #   bootstrap.sh, compile_skill_docs.py
├── docs/                      # MkDocs Material site
│   ├── index.md
│   └── getting-started.md
└── tests/                     # pytest suite
```

## Conventions

### Naming

Skills in this repo follow the pattern `geno-tools-{category}-{verb}` for nested skills,
and `geno-tools-{verb}` for top-level skills. The `name` field in each SKILL.md is the
fully-qualified hyphen-joined path from the skillset root:

- `skills/manager/install/` → `name: geno-tools-manager-install`
- `skills/meta/harness/fork/` → `name: geno-tools-meta-harness-fork`
- `skills/setup/` → `name: geno-tools-setup`


### Adding a new skill

1. Update the umbrella skill table in `skills/geno-tools/SKILL.md` (add to the relevant category row)
2. Update the skills table in this file (`GENO.md`)
3. Run `pytest tests/` to verify skill naming and structure tests pass
4. Bump `version` in `genotools.yaml`, `pyproject.toml`, `package.json`, `plugin.json`,
   `.claude-plugin/plugin.json`, and `geno_tools/__init__.py` if the change is user-facing

### Command prefix aliasing

Slash commands in all committed files (SKILL.md, GENO.md, README.md, docs/) must
always use the canonical `geno-` prefix — e.g. `/geno-tools-manager-install`, not
`/gt-manager-install`. The prefix a user types is configured per-installation in
`~/.geno/config.yaml` and applied at install time. Never hardcode an aliased prefix
in repo source.

### Versioning

The canonical version is `genotools.yaml` → `version`. All other version fields must
match it:

- `pyproject.toml` → `[project] version`
- `package.json` → `version`
- `plugin.json` → `version`
- `.claude-plugin/plugin.json` → `version`
- `geno_tools/__init__.py` → `__version__`

Bump the version when: adding or removing skills, changing CLI subcommand behavior,
or making breaking changes to the manifest schema.

## Architecture

`geno_tools/cli.py` is the argparse entry point. `commands.py` dispatches to handler
functions. `registry.py` resolves skillset names to git URLs via the bundled registry.
`discovery.py` scans GitHub org APIs to find new `geno-*` repos. `paths.py` centralizes
all `~/.geno/` path construction so no other module hardcodes paths.

Bootstrap (`geno_tools/scripts/bootstrap.sh`) is run once by the agent plugin's startup
hook (or manually). It puts `geno-tools` on PATH via `pipx` and seeds `~/.geno/` from
`geno_tools/config/defaults.yaml`.
