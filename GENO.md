# geno-tools

Installer and meta-CLI for geno-* skillsets. Discovers, installs, updates, and manages
the full lifecycle of skills across all supported coding agents.

## Skills table

| Skill | Sub-skillset / Category | Slash command |
|-------|------------------------|---------------|
| geno-tools | — | /geno-tools (umbrella) |
| geno-tools-setup | — | /geno-tools-setup |
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
│   ├── manager/               #   install, remove, update, status, discover, deps, doctor
│   ├── audit/                 #   ecosystem compliance auditor
│   ├── meta/harness/          #   fork / use / promote variant loop
│   ├── meta/ecosystem/        #   discover / scan / onboarding
│   └── author/                #   scaffold skill and repo
├── geno_tools/                # Python package (CLI implementation)
│   ├── cli.py                 #   argparse entry point
│   ├── commands.py            #   subcommand dispatch
│   ├── registry.py            #   skillset registry lookup
│   ├── discovery.py           #   GitHub org scanning
│   ├── paths.py               #   ~/.geno/ path helpers
│   ├── config.py              #   config loading
│   ├── trace.py               #   geno-trace CLI
│   ├── docs.py                #   geno-docs CLI
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
