---
name: geno-tools-system-update
description: >-
  Update geno-tools ITSELF to the latest version (reinstall the CLI + refresh
  the plugin). Use when the user wants to update geno-tools, get the newest
  geno-tools, or after changes land on its main. For skillsets, see `upgrade`.
allowed-tools: "Bash(geno-tools system update *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# system/update — update geno-tools itself

```
geno-tools system update
```

Updates the geno-tools CLI itself to the latest published version. Homebrew is
the install path: `brew upgrade geno-tools` when the running copy lives in a
formula Cellar, falling back to `pipx` from the git remote otherwise.

Installed skillsets are untouched — they have their own lifecycle. Re-register
their skills with `geno-tools update`.

> `system update` = geno-tools itself · `upgrade` = installed skillsets.
