---
name: geno-tools-meta-harness-promote
description: >-
  Promote a winning variant back into a skillset's main. Use when the user wants
  to merge a forked geno-* variant into main after evaluating it.
allowed-tools: "Bash(geno-tools promote *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# meta/harness/promote — merge a variant into main

```
geno-tools promote <name> <variant>
```

Merges the variant branch into main (no upstream push) — the evolve step of the
meta-harness loop. (CLI implementation in progress.)
