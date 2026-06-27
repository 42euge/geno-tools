---
name: geno-tools-tt-repos-list
description: >-
  List repos discovered under the scheme on a host, with session counts and age.
allowed-tools: "Bash(geno-tools tt *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# tt repos/list

```
geno-tools tt repos [--all | -d DOMAIN | -s TERM | -i]
```

Scans the configured repo dirs. Includes interactive (`-i`) and per-domain/search filters; indices feed `new`/`code`.

Hosts are never hardcoded — remote targets resolve from the `[hosts]` table
in `~/.geno/tt/config.toml`. Config + state live under `~/.geno/tt/`.
