---
name: geno-tools-manager-sync
description: >-
  Use when comparing or reconciling geno-tools Stable and active Dev skillset
  selections across computers configured as geno-tt hosts.
allowed-tools: "Bash(geno-tools sync *)"
license: MIT
metadata:
  author: 42euge
  version: "0.11.0"
---

# Synchronize skillset selections

Use the sync commands as the user-facing workflow:

```bash
geno-tools sync status [HOST...]
geno-tools sync push HOST --dry-run
geno-tools sync push HOST --yes
geno-tools sync pull [HOST] --dry-run
geno-tools sync pull [HOST] --yes
```

Interactive push and pull ask Stable or Dev separately for every active Dev
skillset and offer Dev-for-all and Stable-for-all shortcuts. For automation or
a non-TTY command, add `--dev-source active` or `--dev-source stable`.

Dev is a Git-aware snapshot: unpublished commits, staged and unstaged changes,
deletions, and non-ignored untracked files are eligible. Ignored files and
untracked secret, venv, and cache paths stay local, as do Git administration
data and credentials. The destination rebuilds its runtime and keeps the
matching Stable fallback.

After sync, `geno-tools dev deactivate NAME` restores Stable and
`geno-tools dev rollback NAME` restores the selection replaced by sync.

Do not add manual Git remote changes, branch switching, checkout cleanup,
directory copying, or legacy pipx uninstall steps. Sync owns source packaging,
runtime reconstruction, and safe adoption of same-skillset executable links.

See `docs/sync.md` for exclusions, transfer confirmation, and recovery.
