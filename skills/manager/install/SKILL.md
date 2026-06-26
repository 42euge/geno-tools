---
name: geno-tools-manager-install
description: >-
  Install a geno-* skillset (clone, venv, register with all agents). Use when
  the user wants to install or add a geno ecosystem skillset by name, URL, or path.
allowed-tools: "Bash(geno-tools install *) Bash(geno-tools ls *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# manager/install — install a skillset

```
geno-tools install <repo|url|path> [--here]
```

Resolves the source (registry name → git URL, local dir, or git URL), clones it,
creates a per-skillset venv, materializes bin symlinks, and registers its skills
with every agent via `npx skills add --full-depth`. Dependencies declared in
`genotools.yaml` (`requires:`) install first.
