---
name: geno-tools-update
description: Update geno ecosystem skillsets to their latest version
allowed-tools: "Bash(geno-tools update *) Bash(python3 -m genotools update *)"
argument-hint: "[name]  omit to update all"
---

# Update Skillsets

Pull the latest changes for one or all installed geno-* skillsets.

## Input

`$ARGUMENTS` — optional skillset name. If empty, updates all installed skillsets.

## Execution

```bash
geno-tools update $ARGUMENTS
```
