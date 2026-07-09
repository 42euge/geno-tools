---
name: geno-tools-llm-probe
description: >-
  Discover all models on the configured LiteLLM endpoint and benchmark them by
  latency (TTFT + total). Writes rankings to ~/.geno/config.yaml and sets the
  fastest model as the default for smart tab naming and other LLM features.
allowed-tools: "Bash(geno-tools *)"
metadata:
  author: 42euge
  version: "0.7.0"
---

# geno-tools llm probe

Dynamically discovers all models available on a LiteLLM (or any OpenAI-compatible)
endpoint and fires a minimal completion request at each one in parallel to measure
latency. Results are ranked by TTFT (time to first token) and written back to config.

```
geno-tools llm probe
```

**Prerequisites** — configure the endpoint first:
```
geno-tools config set llm.endpoint http://your-litellm:4000
geno-tools config set llm.token sk-...   # stored in ~/.geno/settings.json
```

**Output** — ranked table of all discovered models:
```
#   MODEL                      TTFT    TOTAL   STATUS
1   claude-haiku-4-5           312ms   890ms   ok
2   gpt-4o-mini                445ms   1.2s    ok
3   llama3-8b                  890ms   2.1s    ok
```

Rankings are saved to `~/.geno/config.yaml` under `llm.model_rankings` and the
fastest model is set as `llm.model` automatically. Subsequent `tt name -i` calls
use this model for tab name suggestions.
