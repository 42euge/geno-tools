---
name: geno-tools
description: >-
  Meta-CLI for installing and managing geno-* skillsets.
  Use when user asks about installing, removing, listing, or updating
  geno ecosystem skillsets.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m geno_tools *)"
metadata:
  author: 42euge
  version: "0.3.0"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Its own skills are organized into
category directories (`skills/<category>/<name>/SKILL.md`) — see `SKILLS.md` for
the nesting standard.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. The plugin's SessionStart hook (Claude Code) runs geno_tools/scripts/bootstrap.sh automatically. On Antigravity CLI / Codex, run 'bash \$PLUGIN_ROOT/geno_tools/scripts/bootstrap.sh' once."
```

## Skills by category

| Category | Skills |
|----------|--------|
| **manager/** | `install` · `remove` · `ls` · `update` · `status` · `deps` · `doctor` |
| **audit/** | `run` — ecosystem compliance auditor |
| **meta/harness/** | `fork` · `use` · `promote` — variant evaluate/evolve loop |
| **meta/ecosystem/** | `discover` · `scan` · `onboarding` — find/absorb new skillsets |
| **author/** | `skill` · `repo` — scaffold a skill / a whole skillset repo |

## CLI

- `geno-tools ls [--available]` — list installed / registry skillsets
- `geno-tools install <repo|url|path>` — clone, venv, register with all agents
- `geno-tools remove <repo> [--keep-data]` — uninstall from all agents
- `geno-tools update [repo]` — pull latest + re-register
- `geno-tools deps <repo>` — dependency tree
- `geno-tools discover | scan` — find / queue candidate skillsets

## Source resolution

`<repo>` resolves in order: (1) registered repo name → git URL (bare slug also
accepted), (2) local directory path, (3) git URL (`https://` or `git@`).
