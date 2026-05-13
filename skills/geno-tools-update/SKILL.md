---
name: geno-tools-update
description: >-
  Update installed geno ecosystem skillsets to the latest main branch.
  Use when user says /geno-tools-update, asks to update the ecosystem,
  pull latest, or sync repos.
allowed-tools: "Bash(geno-tools *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
observability:
  success_signal: "all targeted skillsets updated (or confirmed up-to-date) with summary printed"
  failure_signals:
    - "geno-tools update command returned non-zero exit code"
    - "one or more skillsets errored during update"
    - "network error during fetch from origin"
  knowledge_reads:
    - "~/.geno-tools/geno-*/ (installed skillsets to update)"
  knowledge_writes:
    - "~/.geno-tools/geno-*/main/ (updated worktrees)"
---

# geno-tools-update — Update Ecosystem Repos

Pull the latest main branch for installed geno-* skillsets, re-register skills, and reinstall venvs if dependencies changed.

## Usage

Update all installed skillsets:
```bash
geno-tools update
```

Update a single skillset:
```bash
geno-tools update <name>
```

The `<name>` accepts both full (`geno-dev`) and bare (`dev`) forms.

## Behavior

For each skillset the command will:
1. Fetch from origin
2. Fast-forward the main worktree to the latest commit
3. Reinstall the Python venv if `pyproject.toml` changed
4. Re-register skills via `npx skills add` if any SKILL.md files changed

Skillsets are **skipped** (not errored) when:
- The worktree has uncommitted changes (dirty)
- The worktree is on a branch other than the default
- The skillset is in dev mode (local symlink)

A summary is printed at the end showing updated, up-to-date, skipped, and errored repos.
