---
name: geno-tools-meta-harness-use
description: >-
  Select which variant of a forked skillset is active. Use when the user wants
  to switch a geno-* skillset to a specific variant.
allowed-tools: "Bash(geno-tools use *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# meta/harness/use — select a variant

```
geno-tools use <name>@<variant> [--here]
```

Repoints the skillset's `active` symlink to the chosen variant worktree. (CLI
implementation in progress.)
