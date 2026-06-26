---
name: geno-tools-manager-update
description: >-
  Update installed geno-* skillsets to latest main and re-register with all
  agents. Use when the user wants to update or pull the latest skillsets.
allowed-tools: "Bash(geno-tools update *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/update — update skillsets

```
geno-tools update [repo]   # one skillset, or all if omitted
```

`git pull` on each skillset's main worktree, then re-register its skills with
every agent so new/renamed skills surface.
