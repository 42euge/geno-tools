---
name: geno-tools-config-show
description: >-
  Print the current geno ecosystem config from ~/.geno/config.yaml with the
  token redacted. Shows whether a token is set in ~/.geno/settings.json.
allowed-tools: "Bash(geno-tools *)"
metadata:
  author: 42euge
  version: "0.7.0"
---

# geno-tools config show

Print the current configuration, with token redacted for safety.

```
geno-tools config show
```

Shows merged config from `~/.geno/config.yaml` and reports whether a token is
set in `~/.geno/settings.json` (yes/no, never the value).
