---
name: geno-tools-manager-doctor
description: >-
  Verify geno-tools install health — symlinks, worktrees, venvs. Use when the
  user wants to diagnose a broken install or check ecosystem integrity.
allowed-tools: "Bash(geno-tools doctor *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/doctor — verify install health

```
geno-tools doctor
```

Checks each skillset's `active -> main` symlink, worktrees, venv, and bin
symlinks; reports anything broken. (CLI implementation in progress.)
