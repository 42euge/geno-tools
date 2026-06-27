---
name: geno-tools-setup
description: >-
  Install the geno-tools CLI onto your PATH (run this first if `geno-tools`
  isn't found). Ensures pipx, pipx-installs the CLI from the plugin, seeds
  ~/.geno config, and verifies. Use when geno-tools commands report the CLI is
  not on PATH, or right after installing the geno-tools plugin.
allowed-tools: "Bash(bash *) Bash(geno-tools *) Bash(command -v *) Read(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# setup — install the geno-tools CLI

Optional but recommended right after installing the geno-tools plugin. The
plugin's SessionStart hook tries to install the CLI silently; this skill does it
**loudly and reliably**, and is what other skills point you to if the CLI isn't
on PATH.

## Run it

```!
bash "${CLAUDE_PLUGIN_ROOT}/skills/setup/setup.sh"
```

The script (idempotent — safe to re-run):

1. Seeds `~/.geno/config.yaml` from the plugin's `defaults.yaml`.
2. Exits early if `geno-tools` is already on PATH.
3. Locates `pipx` (probing `~/.local/bin` and `~/Library/Python/*/bin`, not just
   PATH) and installs it via Homebrew if truly missing — `pip install --user` is
   blocked on Homebrew Python by PEP 668, so pipx is the reliable path.
4. `pipx install` the CLI from the plugin root.
5. Verifies `geno-tools` resolves and reports the version, or tells you exactly
   how to fix PATH if `~/.local/bin` isn't on it.

## Verify

```
geno-tools ls --available
```

If it still isn't found, the script printed the fix (add `~/.local/bin` to PATH
and open a new shell). The full log is at `~/.geno/bootstrap.log`.
