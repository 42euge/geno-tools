---
name: geno-tools-meta-harness-fork
description: >-
  Fork a skillset into a variant worktree to experiment in isolation. Use when
  the user wants to branch/fork a geno-* skillset to try changes without touching main.
allowed-tools: "Bash(geno-tools fork *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# meta/harness/fork — branch a variant

```
geno-tools fork <name> <variant> [--isolated-venv]
```

Creates a git worktree + branch off the skillset's main as `<variant>`, for the
evaluate step of the meta-harness loop. (CLI implementation in progress.)
