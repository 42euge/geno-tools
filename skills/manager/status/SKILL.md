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

Report, per installed skillset: declared version (`genotools.yaml`), current
commit + branch, and whether the worktree is behind its remote. Surfaces which
skillsets need `geno-tools update`.
