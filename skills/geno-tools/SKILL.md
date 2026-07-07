---
name: geno-tools
description: >-
  Meta-CLI for installing and managing geno-* skillsets.
  Use when user asks about installing, removing, listing, or updating
  geno ecosystem skillsets.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m geno_tools *)"
metadata:
  author: 42euge
  version: "0.6.0"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Its own skills are organized into
category directories (`skills/<category>/<name>/SKILL.md`) — see `SKILLS.md` for
the nesting standard.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH — run /geno-tools-setup to install it (or 'bash \$PLUGIN_ROOT/skills/setup/setup.sh')."
```

## Skills by category

| Category | Skills |
|----------|--------|
| **manager/** | `status` · `discover` · `install` · `remove` · `upgrade` · `update` · `deps` · `doctor` |
| **audit/** | `run` — ecosystem compliance auditor |
| **meta/harness/** | `fork` · `use` · `promote` — variant evaluate/evolve loop |
| **meta/ecosystem/** | `discover` · `scan` · `onboarding` — find/absorb new skillsets |
| **author/** | `skill` · `repo` — scaffold a skill / a whole skillset repo |

## CLI

- `geno-tools status` — installed skillsets: version, commit, drift vs main
- `geno-tools discover [--refresh]` — installable skillsets, grouped by category
- `geno-tools install <repo|url|path>` — clone, venv, register with all agents
- `geno-tools remove <repo> [--keep-data]` — uninstall from all agents
- `geno-tools upgrade [repo]` — upgrade installed skillset(s): pull latest + re-register
- `geno-tools update` — update geno-tools **itself** to the latest version
- `geno-tools deps <repo>` — dependency tree

(`geno-tools ls` = `status`; `ls --available` = `discover`, deprecated aliases.)

## Source resolution

`<repo>` resolves in order: (1) registered repo name → git URL (bare slug also
accepted), (2) local directory path, (3) git URL (`https://` or `git@`).
