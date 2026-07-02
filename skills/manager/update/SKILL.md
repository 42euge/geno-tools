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
2. For every supported agent found on PATH — **Claude Code**, **Codex**,
   **Antigravity** — runs that agent's own headless plugin commands to refresh
   the marketplace and reinstall the plugin (e.g. `claude plugin marketplace
   add` + `claude plugin install`, `codex plugin marketplace upgrade` + `codex
   plugin add`). Agents not installed here are skipped.

The one thing no subprocess can do is reload an *already-running* session, so
the command prints that single per-agent step at the end (e.g. `/reload-plugins`
in Claude Code, or restart Codex). New sessions pick up the plugin automatically.

> `update` = geno-tools itself · `upgrade` = installed skillsets. Don't confuse
> them.
