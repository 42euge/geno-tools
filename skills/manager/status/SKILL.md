---
name: geno-tools-manager-status
description: >-
  Show install status of the geno ecosystem — version, commit, branch, and
  freshness per installed skillset. Use when the user asks about ecosystem
  status, versions, or whether skillsets are out of date.
allowed-tools: "Bash(geno-tools ls *) Bash(git -C * status *) Bash(git -C * log *) Read(*)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/status — ecosystem status

Per installed skillset: declared version (`genotools.yaml`), active variant +
commit, and drift vs the remote (in-sync / behind / ahead / diverged / dirty).
This is exactly what `manager/ls --check` reports — run:

```
geno-tools ls --check
```

Surfaces which skillsets `geno-tools update` would advance.
