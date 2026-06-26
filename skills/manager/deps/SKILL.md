---
name: geno-tools-manager-deps
description: >-
  Show the dependency tree for a geno-* skillset. Use when the user asks what a
  skillset requires or wants to inspect transitive dependencies.
allowed-tools: "Bash(geno-tools deps *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/deps — dependency tree

```
geno-tools deps <repo>
```

Resolves `requires:` from `genotools.yaml` recursively and prints the tree.
