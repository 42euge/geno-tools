---
name: geno-tools-config-set
description: >-
  Set a geno ecosystem config value by dot-path key. Endpoint and model go to
  ~/.geno/config.yaml; the token goes to ~/.geno/settings.json (never in config).
allowed-tools: "Bash(geno-tools *)"
metadata:
  author: 42euge
  version: "0.7.0"
---

# geno-tools config set

Set any config value using a dot-path key.

```
geno-tools config set <key> <value>
```

**Common keys:**
```
geno-tools config set llm.endpoint http://litellm.local:4000
geno-tools config set llm.token sk-...         # → ~/.geno/settings.json
geno-tools config set llm.model claude-haiku-4-5
geno-tools config set llm.timeout 15
geno-tools config set aliases.command_prefix geno
```

Token values (`llm.token`) are automatically routed to `~/.geno/settings.json`
so `~/.geno/config.yaml` remains safe to version-control. All other values go
into `~/.geno/config.yaml`.
