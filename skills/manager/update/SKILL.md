---
name: geno-tools-manager-update
description: >-
  Update geno-tools ITSELF to the latest version (reinstall the CLI + refresh
  the plugin). Use when the user wants to update geno-tools, get the newest
  geno-tools, or after changes land on its main. For skillsets, see `upgrade`.
allowed-tools: "Bash(geno-tools update *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/update — update geno-tools itself

```
geno-tools update
```

Updates the geno-tools meta-tool to the latest published version:

1. Reinstalls the `geno-tools` CLI from GitHub via `pipx` (the binary on PATH).
2. Refreshes the Claude Code marketplace clone so a plugin reinstall pulls latest.

A CLI subprocess can't issue Claude Code's slash commands, so the final reload
is yours to run — the command prints it:

```
/plugin install geno-tools@geno-tools
/reload-plugins
```

> `update` = geno-tools itself · `upgrade` = installed skillsets. Don't confuse
> them.
