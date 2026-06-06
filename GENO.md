# geno-tools — Skills-Only Geno Skillset Catalog

`geno-tools` is now a skills-only repo in the geno ecosystem. It ships no Python runtime CLI and no installation bootstrap scripts.

@./VISION.md
@./TENETS.md

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-tools | — | — (umbrella) |
| geno-alias | — | /geno-alias |
| geno-audit | — | /geno-audit |
| geno-icons | — | /geno-icons |
| geno-onboarding | — | /geno-onboarding |
| geno-data-workspaces-init | — | /geno-data-workspaces-init |
| geno-skills-create | — | /geno-skills-create |
| geno-skills-install | — | /geno-skills-install |
| geno-skills-status | — | /geno-skills-status |
| geno-tools-open-docs | — | /geno-tools-open-docs |
| geno-tools-sessions-spawn | — | /geno-tools-sessions-spawn |
| geno-tools-create-skillset-repo | — | /geno-tools-create-skillset-repo |
| geno-tools-improve | — | /geno-tools-improve |
| geno-tools-update | — | /geno-tools-update |

## Repo structure

```
geno-tools/
├── GENO.md                        # agent instructions (this file)
├── SKILL.md -> skills/geno-tools/SKILL.md  # umbrella skill manifest
├── genotools.yaml                 # skillset manifest
├── CLAUDE.md                      # Claude Code pointer -> GENO.md
├── GEMINI.md                      # legacy pointer -> GENO.md
├── AGENTS.md                      # Codex and Antigravity pointer -> GENO.md
├── gemini-extension.json          # legacy extension descriptor
├── package.json                   # plugin metadata (non-executable)
├── skills/                        # skill definitions
│   ├── geno-tools/SKILL.md        # umbrella skill
│   ├── geno-alias/SKILL.md        # custom skill aliasing
│   ├── geno-audit/SKILL.md        # ecosystem compliance auditor
│   ├── geno-icons/SKILL.md        # pixel art icon generator
│   ├── geno-onboarding/SKILL.md   # skillset onboarding wizard
│   ├── geno-data-workspaces-init/SKILL.md  # data workspace scaffolder
│   ├── geno-skills-create/SKILL.md #  skill scaffolder
│   ├── geno-skills-install/SKILL.md #  local skill installer
│   ├── geno-skills-status/SKILL.md #  ecosystem status reporter
│   ├── geno-tools-improve/SKILL.md #  self-improvement cycle
│   ├── geno-tools-update/SKILL.md #   ecosystem updater
│   ├── geno-tools-open-docs/SKILL.md      # docs site opener
│   ├── geno-tools-sessions-spawn/SKILL.md  # session launcher
│   └── geno-tools-create-skillset-repo/SKILL.md # skillset scaffolder
├── docs/                          # MkDocs Material documentation site
├── .claude-plugin/plugin.json     # Claude Code plugin manifest
├── .codex-plugin/plugin.json      # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json     # Cursor plugin manifest
├── plugin.json                    # Antigravity plugin manifest
├── .opencode/                     # OpenCode plugin
└── LICENSE                        # MIT license
```

## Conventions

### Command prefix aliasing

Slash commands in this repo use the canonical `geno-` prefix (e.g. `/geno-tools-update`, `/geno-audit`). Prefix preferences are handled by the host runtime.

### Versioning

The canonical version is in `genotools.yaml`. Bump it when you add/remove skills, change skill behavior, or update agent-facing docs.

### Adding a new skill

To add a skill:

1. Add `skills/<name>/SKILL.md` with `name` and `description` frontmatter.
2. If the skill has subcommands, create one directory per sub-skill.
3. Add it to the skills table in this file and the umbrella SKILL.md.
4. Add/refresh docs under `docs/skills/` for the new skill if needed.
5. Update this repo's version in `genotools.yaml`.

### Plugin structure

This repo has plugin descriptors so it can be loaded by supported agents without installing any Python tooling:

- `.claude-plugin/plugin.json`
- `.codex-plugin/plugin.json`
- `.cursor-plugin/plugin.json`
- `plugin.json` (Antigravity)
- `.opencode/plugins/geno-tools.js`

All manifests point at `./skills`.
