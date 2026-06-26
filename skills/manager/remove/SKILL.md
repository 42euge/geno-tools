---
name: geno-tools-manager-remove
description: >-
  Uninstall a geno-* skillset from all agents (exact-removal). Use when the user
  wants to remove or uninstall a geno ecosystem skillset.
allowed-tools: "Bash(geno-tools remove *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/remove — uninstall a skillset

```
geno-tools remove <repo> [--keep-data]
```

Replays install in reverse: unregisters every skill via `npx skills remove`,
removes bin symlinks, and deletes the skillset tree. `--keep-data` preserves
`venvs/` and any local data.
