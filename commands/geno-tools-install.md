---
name: geno-tools-install
description: Install a geno ecosystem skillset from registry, path, or git URL
allowed-tools: "Bash(geno-tools install *) Bash(python3 -m genotools install *)"
argument-hint: "<name|url|path>  e.g. 'media', 'kaggle', 'https://github.com/user/geno-foo.git'"
---

# Install Skillset

Install a geno-* skillset. Accepts a registry short name, local path, or git URL.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. Install: pipx install git+https://github.com/42euge/geno-tools.git"
```

## Input

`$ARGUMENTS` — the skillset to install.

If `$ARGUMENTS` is empty, run `geno-tools ls --available` to show the registry and ask the user which one to install.

## Execution

```bash
geno-tools install $ARGUMENTS
```

This will:
1. Resolve the source (registry name, local path, or git URL)
2. Bare-clone the repo + create a main worktree under `~/.geno-tools/geno-{name}/`
3. Create an isolated venv and install dependencies if the skillset has a `pyproject.toml`
4. Symlink CLI binaries into `~/.local/bin/`
5. Register skills with all supported agents (Claude Code, Codex, etc.) via `npx skills add`

If the skillset is already installed, report the error and suggest `geno-tools remove <name>` first.
