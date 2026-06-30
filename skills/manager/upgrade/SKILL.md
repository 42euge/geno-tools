---
name: geno-tools-manager-upgrade
description: >-
  Upgrade installed geno-* skillsets to their latest main and re-register with
  all agents. Use when the user wants to update/pull the latest skillsets. For
  updating geno-tools itself, see `update`.
allowed-tools: "Bash(geno-tools upgrade *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/upgrade — upgrade installed skillsets

```
geno-tools upgrade [name]   # one skillset, or all if omitted
```

`git pull --ff-only` on each installed skillset's main worktree, then re-register
its skills with every agent so new/renamed skills surface. Dirty or diverged
worktrees are skipped (reported, not clobbered).

Run `geno-tools status` first to see which skillsets are behind.

> `upgrade` = installed skillsets · `update` = geno-tools itself.
