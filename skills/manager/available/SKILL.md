---
name: geno-tools-manager-available
description: >-
  List geno-* skillsets you can install (from the discovery cache), marking
  which are already installed. Use when the user wants to browse or find
  installable skillsets. Replaces `geno-tools ls --available`.
allowed-tools: "Bash(geno-tools available *) Bash(geno-tools ls *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/available — what you can install

```
geno-tools available
```

Lists every discoverable skillset from the registry cache, with `✓ installed`
on the ones you already have:

```
geno-tools
── available · 19 ──────────────────────────────
  geno-loops    ✓ installed
  geno-mon      https://github.com/42euge/geno-mon.git
  ...
```

If the cache is empty, run `/geno-tools-meta-ecosystem-discover` to populate it
(curl-based discovery — see that skill). Install one with
`geno-tools install <name>`.
