---
name: geno-tools-meta-ecosystem-discover
description: >-
  List candidate geno-* skillsets from configured discovery sources. Use when
  the user wants to find installable skillsets across their orgs/registries.
allowed-tools: "Bash(geno-tools discover *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# meta/ecosystem/discover — find candidate skillsets

```
geno-tools discover [--dry-run]
```

Lists repos from `~/.geno/config.yaml` `discovery.sources` that match the
configured prefix and carry a top-level `SKILL.md` — the candidates you can
`geno-tools install`.
