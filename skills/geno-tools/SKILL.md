---
name: geno-tools
description: >-
  Geno skillset lifecycle and dependency manager. Use when the user asks about
  discovering, installing, removing, or updating geno skillsets.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m geno_tools *)"
metadata:
  author: 42euge
  version: "0.9.0"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Its own skills are organized into
category directories (`skills/<category>/<name>/SKILL.md`) — see
`docs/skillsets.md` for the layout standard.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH — run /geno-tools-setup to install it (or 'bash \$PLUGIN_ROOT/skills/setup/setup.sh')."
```

## Skills by category

| Category | Skills |
|----------|--------|
| **manager/** | `status` · `discover` · `install` · `remove` · `upgrade` · `update` · `deps` |
| **meta/ecosystem/** | `discover` · `scan` · `onboarding` — find/absorb new skillsets |
| **author/** | `skill` · `repo` — scaffold a skill / a whole skillset repo |
| **config/** | `show` · `set` — read/write `~/.geno/config.yaml` |

Registration itself is delegated to `npx skills`; geno-tools adds skillset
lifecycle and dependency resolution.

## CLI

- `geno-tools status` — installed skillsets: version, commit, drift vs main
- `geno-tools skills discover [--refresh]` — installable skillsets, grouped by category
- `geno-tools skills install <repo|url|path>` — clone, venv, register with all agents
- `geno-tools skills remove <repo> [--keep-data]` — uninstall from all agents
- `geno-tools skills upgrade [repo]` — upgrade installed skillset(s): pull latest + re-register
- `geno-tools update` — update geno-tools **itself** to the latest version
- `geno-tools skills uninstall [--dry-run]` — fully remove geno-tools (inverse of install; keeps your data)
- `geno-tools skills deps <repo>` — dependency tree

## Source resolution

`<repo>` resolves in order: (1) registered repo name → git URL (bare slug also
accepted), (2) local directory path, (3) git URL (`https://` or `git@`).
