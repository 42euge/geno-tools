# geno-tools

Geno skillset control plane. Raw skill registration is delegated to
`npx skills`; geno-tools owns discovery, installation, upgrades, removal, and
transitive `requires:` dependency resolution.

Two layers:
- **`npx skills`** (external) — per-agent skill registration.
- **geno-tools** — skillset lifecycle and dependency resolution.

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
| geno-tools-meta-ecosystem-discover | meta/ecosystem | /geno-tools-meta-ecosystem-discover |
| geno-tools-meta-ecosystem-scan | meta/ecosystem | /geno-tools-meta-ecosystem-scan |
| geno-tools-meta-ecosystem-onboarding | meta/ecosystem | /geno-tools-meta-ecosystem-onboarding |
| geno-tools-author-skill | author | /geno-tools-author-skill |
| geno-tools-author-repo | author | /geno-tools-author-repo |
| geno-tools-config-show | config | /geno-tools-config-show |
| geno-tools-config-set | config | /geno-tools-config-set |

## Repo structure

```
geno-tools/
├── AGENTS.md                  # agent instructions (this file) — read by every agent
├── SKILL.md                   # umbrella skill manifest (root-level convenience copy)
├── SKILLS.md                  # skill nesting standard reference doc
├── pyproject.toml             # Python package definition (canonical version)
├── package.json               # JS metadata (version parity with pyproject.toml)
├── plugin.json                # cross-agent plugin manifest
├── marketplace.json           # plugin marketplace catalog
├── skills/                    # skill definitions (nested category tree)
│   ├── geno-tools/SKILL.md    #   umbrella skill
│   ├── setup/SKILL.md         #   PATH setup
│   ├── manager/               #   install, remove, upgrade, update, status, discover, deps
│   ├── meta/ecosystem/        #   discover / scan / onboarding
│   ├── author/                #   scaffold skill and repo
│   └── config/                #   show / set
├── geno_tools/                # Python package (CLI implementation)
│   ├── cli.py                 #   argparse entry point
│   ├── core/                  #   geno-tools self-management module
│   │   ├── commands.py        #     update/config commands
│   │   ├── config.py          #     config loading
│   │   ├── terminal.py        #     shared terminal formatting
│   │   └── config/defaults.yaml
│   └── skills_manager/        #   managed-skillset module
│       ├── commands/          #     lifecycle parser and one module per command
│       │   ├── install.py
│       │   ├── uninstall.py
│       │   ├── upgrade.py
│       │   ├── remove.py
│       │   ├── deps.py
│       │   ├── discover.py
│       │   └── scan.py
│       ├── agents.py          #     installed coding-agent detection
│       ├── registry.py        #     skillset registry lookup
│       ├── discovery.py       #     source-provider scanning
│       └── paths.py           #     managed-state paths
├── docs/                      # docs source
└── tests/                     # pytest suite
```

## Conventions

### Naming

Skills in this repo follow the pattern `geno-tools-{category}-{verb}` for nested skills,
and `geno-tools-{verb}` for top-level skills. The `name` field in each SKILL.md is the
fully-qualified hyphen-joined path from the skillset root:

- `skills/manager/install/` → `name: geno-tools-manager-install`
- `skills/meta/ecosystem/scan/` → `name: geno-tools-meta-ecosystem-scan`
- `skills/setup/` → `name: geno-tools-setup`

### Adding a new skill

1. Update the umbrella skill table in `skills/geno-tools/SKILL.md` (add to the relevant category row)
2. Update the skills table in this file (`AGENTS.md`)
3. If the skill sits in a new category dir, add that dir to `plugin.json` → `skills[]`
4. Run `pytest tests/` to verify skill naming and structure tests pass
5. Bump the version everywhere listed under **Versioning** below, if the change is user-facing

### Command prefix aliasing

Slash commands in all committed files (SKILL.md, AGENTS.md, README.md) must
always use the canonical `geno-` prefix — e.g. `/geno-tools-manager-install`, not
`/gt-manager-install`. The prefix a user types is configured per-installation in
`~/.geno/config.yaml` and applied at install time. Never hardcode an aliased prefix
in repo source.

### Versioning

The canonical version is `pyproject.toml` → `[project] version`. All other version
fields must match it:

- `package.json` → `version`
- `plugin.json` → `version`
- `marketplace.json` → `plugins[0].version`
- `geno_tools/__init__.py` → `__version__`
- `SKILL.md` and `skills/geno-tools/SKILL.md` → `metadata.version`

Bump the version when: adding or removing skills, changing CLI subcommand behavior,
or making breaking changes to the manifest schema.

## Architecture

`geno_tools/cli.py` is the argparse entry point. The `core` module owns
geno-tools' configuration, self-update behavior, and shared terminal output.
The `skills_manager` module owns skillset lifecycle commands, discovery,
registry lookup, agent detection, and managed-state paths.
