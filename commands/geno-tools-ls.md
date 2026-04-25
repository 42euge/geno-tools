---
name: geno-tools-ls
description: List installed geno ecosystem skillsets or show the available registry
allowed-tools: "Bash(geno-tools ls *) Bash(python3 -m genotools ls *)"
argument-hint: "[--available]"
---

# List Skillsets

Show installed geno-* skillsets and their active variant, or list the full registry.

## Input

`$ARGUMENTS` — pass `--available` to show the registry instead of installed skillsets.

## Execution

```bash
geno-tools ls $ARGUMENTS
```
