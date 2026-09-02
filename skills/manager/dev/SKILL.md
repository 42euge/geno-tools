---
name: geno-tools-manager-dev
description: >-
  Use when the user wants an installed skillset to run from a local development
  checkout, inspect which checkout is active, or return it to the stable copy.
allowed-tools: "Bash(geno-tools dev *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/dev — select a skillset development checkout

Use geno-tools dev mode instead of creating or activating a virtual environment
inside the checkout. The skillset must already be installed.

Activate a local checkout:

```bash
geno-tools dev activate /absolute/path/to/geno-tt
```

Activation keeps the managed stable checkout untouched while atomically
selecting the local source, an isolated editable runtime, its console-script
links, and its registered agent skills. Confirm the selection before running a
skillset command:

```bash
geno-tools dev status geno-tt
command -v tt
tt --version
```

`geno-tools dev status` without a name lists every installed skillset. It exits
nonzero when the active source, runtime links, and saved selection disagree.

Return to the managed stable checkout and runtime with:

```bash
geno-tools dev deactivate geno-tt
```

Do not manually repoint `~/.geno-tools/<name>/active` or links in
`~/.local/bin`; use these commands so source, runtime, and skills stay aligned.
