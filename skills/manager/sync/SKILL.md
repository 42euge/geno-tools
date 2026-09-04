---
name: geno-tools-manager-sync
description: >-
  Use when comparing or reconciling geno-tools skillset installations across
  computers configured as geno-tt hosts.
allowed-tools: "Bash(geno-tools sync *)"
license: MIT
metadata:
  author: 42euge
  version: "0.11.0"
---

# manager/sync — reconcile installations across computers

Check installation and portable-config drift without changing either machine:

```bash
geno-tools sync status
```

Make this machine match the configured primary, previewing first:

```bash
geno-tools sync pull --dry-run
geno-tools sync pull --yes
```

Or make a named host match this machine:

```bash
geno-tools sync push HOST --dry-run
geno-tools sync push HOST --yes
```

Sync reconciles installed skillset repositories through the normal install,
update, and uninstall lifecycle. It transfers no worktrees, venvs, credentials,
dev-mode selections, or uncommitted files. Dirty managed worktrees stop
reconciliation before the first mutation.

See `docs/sync.md` for setup, authority, and recovery details.
