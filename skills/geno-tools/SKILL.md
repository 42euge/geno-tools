---
name: geno-tools
description: >-
  Geno skillset lifecycle and dependency manager. Use when the user asks about
  discovering, installing, removing, updating, synchronizing across computers,
  or selecting a development checkout for geno skillsets, or making the current
  coding-agent session persistent in tmux.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m geno_tools *)"
metadata:
  author: 42euge
  version: "0.11.0"
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
| **manager/** | `status` · `discover` · `install` · `remove` · `upgrade` · `dev` · `sync` |
| **system/** | `update` — manage the geno-tools installation itself |
| **session/** | `persist` — resume the current agent conversation inside tmux |
| **meta/ecosystem/** | `discover` · `scan` · `onboarding` — find/absorb new skillsets |
| **author/** | `skill` · `repo` — scaffold a skill / a whole skillset repo |
| **config/** | `show` · `set` — read/write `~/.geno/config.yaml` |

Registration itself is delegated to `npx skills`; geno-tools adds skillset
lifecycle and dependency resolution.

## CLI

- `geno-tools status` — installed skillsets: version, commit, drift vs main
- `geno-tools discover [--refresh]` — installable skillsets, grouped by category
- `geno-tools install <repo|url|path>` — clone, venv, register with all agents
- `geno-tools uninstall <repo> [--keep-data]` — uninstall from all agents
- `geno-tools update [repo]` — update installed skillset(s): pull latest + re-register
- `geno-tools dev activate <checkout>` — select local source, runtime, commands, and skills
- `geno-tools dev status [repo]` — show stable/dev selection and detect drift
- `geno-tools dev deactivate <repo>` — restore the managed stable checkout
- `geno-tools sync status|pull|push` — compare or reconcile installations across geno-tt hosts
- `geno-tools system update` — update geno-tools **itself** to the latest version
- `geno-tools system uninstall [--dry-run]` — guarded removal of all geno-tools-managed files; keeps user data

## Source resolution

`<repo>` resolves in order: (1) registered repo name → git URL (bare slug also
accepted), (2) local directory path, (3) git URL (`https://` or `git@`).
