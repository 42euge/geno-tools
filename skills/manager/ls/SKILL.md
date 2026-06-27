---
name: geno-tools-manager-ls
description: >-
  List installed geno-* skillsets (or all available in the registry). Use when
  the user asks what skillsets are installed or available.
allowed-tools: "Bash(geno-tools ls *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/ls — list skillsets

```
geno-tools ls               # installed: version · variant@commit
geno-tools ls --check       # also compare each to its remote main (network)
geno-tools ls --available   # all discoverable skillsets in the registry cache
```

Plain `ls` shows each installed skillset's declared version (`genotools.yaml`),
active variant, and short commit — no network. `--check` adds a state column:
`in-sync`, `behind (<remote-sha>)`, `ahead`, `diverged`, `dirty`, or `offline`,
so you can see which skillsets `geno-tools update` would advance.

