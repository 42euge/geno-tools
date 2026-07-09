---
name: geno-tools-llm-suggest
description: >-
  Use the configured LLM to suggest a dot-notation workspace name from a terminal
  tab's context (cwd, running job, raw title). Used by tt name -i to pre-fill
  suggestions during interactive tab naming.
allowed-tools: "Bash(geno-tools *)"
metadata:
  author: 42euge
  version: "0.7.0"
---

# geno-tools llm suggest

Asks the configured LLM to generate a dot-notation workspace name (e.g.
`bluebeam.rf.receiver`, `ngrt.ct.deploy`) from a terminal tab's context.

```
geno-tools llm suggest --cwd /path/to/dir --job claude --title "raw tab title"
```

Prints the suggested name to stdout and exits. Empty output means no LLM is
configured or the request failed — callers should fall back to manual input.

**Used by:** `tt name -i` — the interactive tab naming walk-through calls this
automatically for each unnamed tab and presents the suggestion as a pre-filled default.

**Options:**
- `--cwd`    Working directory of the tab
- `--job`    Running job/process name (e.g. `claude`, `zsh`, `python`)
- `--title`  Raw tab title as shown in iTerm2
- `--model`  Override the model (default: top ranked from `geno-tools llm probe`)
