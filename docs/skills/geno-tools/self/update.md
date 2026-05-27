---
title: geno-tools-update
description: Update installed geno ecosystem skillsets to the latest main branch
---

# geno-tools-update

`/geno-tools-update`

> Update installed geno ecosystem skillsets to the latest main branch

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

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

</div>

<div class="zoom-section zoom-section-4" markdown>

---

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

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-tools-update \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = all targeted skillsets updated or confirmed up-to-date
- `failure` = geno-tools update command errored, fetch failed, or one or more skillsets could not update
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
