# Getting Started

## Prerequisites

- Git
- Node.js (for `npx skills`)
- Python 3.11+ (for the CLI install path)

## Install geno-tools

geno-tools can be installed as a **Claude Code plugin** or as a **standalone CLI** — pick whichever fits your workflow, or use both.

### Option A: Claude Code plugin

```bash
claude /plugin install 42euge/geno-tools
```

This gives you `/gt-install`, `/gt-remove`, `/gt-ls`, and `/gt-update` slash commands inside Claude Code. The plugin wraps the CLI, so you still need the CLI on your PATH for the slash commands to work:

```bash
pipx install git+https://github.com/42euge/geno-tools
```

### Option B: CLI only

```bash
pipx install git+https://github.com/42euge/geno-tools
```

Or with pip:

```bash
pip install git+https://github.com/42euge/geno-tools
```

Verify the install:

```bash
geno-tools --version
```

## Install your first skillset

List what's available in the registry:

```bash
geno-tools ls --available
```

```
  agents       https://github.com/42euge/geno-agents.git
  media        https://github.com/42euge/geno-media.git
  research     https://github.com/42euge/geno-research.git
  taxes        https://github.com/42euge/geno-taxes.git
  kaggle       https://github.com/42euge/geno-kaggle.git
  dev          https://github.com/42euge/geno-dev.git
```

Install one:

```bash
geno-tools install media
```

This clones the repo, sets up any declared venvs, and wires the skill into your coding agent (slash commands appear immediately).

## Check what's installed

```bash
geno-tools ls
```

```
  geno-media               active: main
```

## Develop a skillset locally

If you're hacking on a skillset, use `dev` to symlink your local checkout instead of cloning:

```bash
geno-tools dev media ~/src/geno-media
```

Edits to your local checkout take effect immediately — no reinstall needed.

## What's next?

- [CLI Reference](cli-reference.md) — full command documentation
- [Creating a Skillset](skillsets/creating.md) — build your own
- [Variants & Worktrees](architecture/variants.md) — experiment with `fork` and `use`
