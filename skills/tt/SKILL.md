---
name: geno-tools-tt
description: >-
  Terminal/session + workspace manager. Use when the user wants to create or
  navigate code workspaces (inv, new-project), manage whole-workspace git
  worktrees (wt), or attach to remote tmux sessions across hosts.
allowed-tools: "Bash(geno-tools tt *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-tools tt — terminal/session + workspace manager

Vendored terminal-tools. Manages the code-org scheme
(`~/code/<track>/<domain>/<workspace>.<born>/<repo>`), whole-workspace git
worktrees, and remote tmux sessions across configured hosts (`~/.geno/tt/config.toml`).

The interactive `tt` shell function (cd-into-target + iTerm track tinting) is
installed by the SessionStart bootstrap; non-interactive use works directly via
`geno-tools tt …`.

## Workspaces
- `geno-tools tt inv [-t TRACK] [-d DOMAIN] [--expand]` — inventory tree: `track/domain/workspace.born [N repos · M wt]`
- `geno-tools tt new-project <track>.<domain>.<workspace>[.<repo>]` — scaffold a workspace + first repo
- `geno-tools tt -H <host> new-project …` — scaffold on a remote host over SSH

## Worktrees (whole-workspace)
- `geno-tools tt wt new|ls|cd|rm <name> [-w WORKSPACE]` — git-worktree every repo in a workspace at once (branch `wt/<name>`); `-w` + `-H` drives a remote host

## Sessions (remote tmux)
- `geno-tools tt ls | <target> | new | kill | clean | recover` — manage tmux sessions
- `geno-tools tt repos | tui | hosts | add-host | theme | profile` — repos, TUI, host + appearance config

## Notes
- Interactive `cd` and iTerm tab-tinting require the `tt` shell function (sourced from `~/.geno/tt/init.sh` by bootstrap). `geno-tools tt` itself is pure.
- Config + state live at `~/.geno/tt/` (legacy `~/.tt/` read as fallback).
