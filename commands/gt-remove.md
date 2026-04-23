---
name: gt-remove
description: Uninstall a geno ecosystem skillset
allowed-tools: "Bash(geno-tools remove *) Bash(python3 -m genotools remove *)"
argument-hint: "<name> [--keep-data]"
---

# Remove Skillset

Uninstall a geno-* skillset and clean up all its artifacts.

## Input

`$ARGUMENTS` — the skillset name to remove (e.g. `media`, `kaggle`).

If `$ARGUMENTS` is empty, run `geno-tools ls` to show installed skillsets and ask which one to remove.

## Execution

```bash
geno-tools remove $ARGUMENTS
```

Use `--keep-data` to preserve venvs and worktrees while removing the repo and skill registrations.
