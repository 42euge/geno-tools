---
name: geno-tools-manager-discover
description: >-
  Find and list installable geno-* skillsets, grouped by category, with
  ✓ installed markers. Use when the user wants to browse, find, or discover
  skillsets to install. Replaces `geno-tools available`.
allowed-tools: "Bash(geno-tools skills discover *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/discover — find skillsets to install

```
geno-tools skills discover            # grouped list (auto-refreshes if >30min stale)
geno-tools skills discover --refresh  # force a fresh network scan
```

Lists every installable skillset grouped by ecosystem category (read from each
repo's `layer.json`), marking what you already have:

```
geno-tools
── discover · 19 ────────────────────────────────
  Core Framework
    geno-audit     https://github.com/42euge/geno-audit.git
    geno-iso       https://github.com/42euge/geno-iso.git
  Developer Tools
    geno-loops     ✓ installed
    geno-dev       https://github.com/42euge/geno-dev.git
  ...
```

Discovery uses unauthenticated `curl` against the public GitHub API (no `gh`, no
token) — public repos only. The list is cached at `~/.geno/registry.json` and
auto-refreshed when older than 30 minutes; `--refresh` forces it. Install one
with `geno-tools skills install <name>`.
