---
title: geno-mine-extract
description: Run the full session mining pipeline
---

# geno-mine-extract

`/geno-mine-extract "[--since <days>d] [--skill <name>] [--format sft,dpo] [--dry-run]"`

> Run the full session mining pipeline

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

Run the full mining pipeline:

1. Load traces from `~/.geno/traces/`
2. Correlate with session transcripts in `~/.claude/projects/`
3. Classify segments by training value (tier 1/2/3)
4. Generate examples in requested formats
5. Apply privacy filters (path scrubbing, secret detection, PII removal)
6. Save to `~/.geno/datasets/`

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Run the pipeline

```bash
geno-mine extract [--since 30d] [--skill <name>] [--format sft,dpo] [--max-tier 2] [--dry-run]
```

Parse `$ARGUMENTS` and pass them to the CLI.

### 2. Review results

Show the user what was generated:
- Number of traces processed
- Segments correlated
- Tier distribution (tier 1/2/3)
- Examples generated per format
- Dataset location

### 3. Suggest next steps

- `geno-mine stats` to see overall dataset statistics
- `geno-mine export --format sft` to export for finetuning
- Run again with different filters to expand the dataset

## Completion

```bash
geno-trace emit \
  --skill geno-mine-extract \
  --status <success|failure> \
  --tool-calls <count> \
  --errors <count> \
  --produced "~/.geno/datasets/"
```

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-mine](index.md)
