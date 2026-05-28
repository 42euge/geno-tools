---
title: geno-mine-export
description: Export a dataset version to a directory for finetuning
---

# geno-mine-export

`/geno-mine-export "--format <sft|dpo|tool_trace|anthropic> [--version <tag>] [-o <dir>]"`

> Export a dataset version to a directory for finetuning

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

Export a mined dataset version to a local directory for use with finetuning pipelines.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

```bash
geno-mine export --format <sft|dpo|tool_trace|anthropic> [--version <tag>] [-o <output-dir>]
```

Defaults to the latest version. Copies the dataset files and metadata to the output directory.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-mine](index.md)
