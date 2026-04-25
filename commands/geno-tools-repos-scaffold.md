---
name: geno-tools-repos-scaffold
description: Scaffold a new geno-ecosystem repository with all required conventions
argument-hint: "<name> [--description 'short description'] [--python] [--docker]"
---

# Scaffold New Geno Repo

Create a new `geno-{name}` repository following ecosystem conventions.

## Input

`$ARGUMENTS` — the short name for the new repo (e.g. `foo` creates `geno-foo`).

If `$ARGUMENTS` is empty, ask the user for the name and description.

## Execution

Invoke the `geno-tools-repos-scaffold` skill to scaffold the repository. The skill handles all file generation, git init, and reporting.
