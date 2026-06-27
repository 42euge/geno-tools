---
name: geno-tools-tt-sessions-tui
description: >-
  Open the interactive TUI session browser.
allowed-tools: "Bash(geno-tools tt *) Bash(python3 -m geno_tools.tt *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# tt sessions/tui

```
geno-tools tt tui [refresh_s]
```

Textual-based arrow-key browser for sessions/repos (requires the `tui` extra: `pipx inject geno-tools textual`).

Hosts are never hardcoded — remote targets resolve from the `[hosts]` table
in `~/.geno/tt/config.toml`. Config + state live under `~/.geno/tt/`.
