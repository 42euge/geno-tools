---
name: geno-tools-meta-ecosystem-scan
description: >-
  Scan for new uninstalled geno-* skillsets and queue them as candidates. Use
  when the user wants to absorb newly-published skillsets into the ecosystem.
allowed-tools: "Bash(geno-tools skills scan *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# meta/ecosystem/scan — queue new skillsets

```
geno-tools skills scan [--namespace <ns>] [--dry-run]
```

Discovers skillsets not yet installed and queues them as candidates — the
absorb step of the ecosystem lifecycle.
