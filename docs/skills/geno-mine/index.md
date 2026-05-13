---
title: geno-mine
description: Session mining — extract, analyze, and export agent session data
---

# geno-mine

Session mining — extract, analyze, and export agent session data

[:material-github: GitHub](https://github.com/42euge/geno-mine){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-mine-export](#geno-mine-export) | `/geno-mine-export` | Export a dataset version to a directory for finetuning |
| [geno-mine-extract](#geno-mine-extract) | `/geno-mine-extract` | Run the full session mining pipeline |
| [geno-mine-stats](#geno-mine-stats) | `/geno-mine-stats` | Show dataset statistics |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-mine
    
    Session mining toolkit for the geno ecosystem. Extracts finetuning datasets
    from Claude Code session transcripts by correlating structured skill traces
    with raw JSONL transcripts, classifying segments by training value, and
    generating examples in multiple formats (SFT, DPO, tool traces, Anthropic).
    
    ## Sub-skills
    
    | Skill | Slash command | Purpose |
    |-------|---------------|---------|
    | geno-mine-extract | /geno-mine-extract | Run the full mining pipeline |
    | geno-mine-stats | /geno-mine-stats | Show dataset statistics |
    | geno-mine-export | /geno-mine-export | Export datasets to external formats |

## geno-mine-export

**Slash command:** `/geno-mine-export`

> Export a dataset version to a directory for finetuning

??? example "Full skill definition (Level 4)"

    Export a mined dataset version to a local directory for use with finetuning pipelines.
    
    ## Workflow
    
    ```bash
    geno-mine export --format <sft|dpo|tool_trace|anthropic> [--version <tag>] [-o <output-dir>]
    ```
    
    Defaults to the latest version. Copies the dataset files and metadata to the output directory.

## geno-mine-extract

**Slash command:** `/geno-mine-extract`

> Run the full session mining pipeline

??? info "Observability"

    success_signal: "dataset saved with >0 examples" failure_signals: - "no traces found" - "no segments correlated" - "all segments filtered" knowledge_reads: - "~/.geno/traces/ (structured skill traces)" - "~/.claude/projects/ (session transcripts)" knowledge_writes: - "~/.geno/datasets/ (training examples)"

??? example "Full skill definition (Level 4)"

    Run the full mining pipeline:
    
    1. Load traces from `~/.geno/traces/`
    2. Correlate with session transcripts in `~/.claude/projects/`
    3. Classify segments by training value (tier 1/2/3)
    4. Generate examples in requested formats
    5. Apply privacy filters (path scrubbing, secret detection, PII removal)
    6. Save to `~/.geno/datasets/`
    
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

## geno-mine-stats

**Slash command:** `/geno-mine-stats`

> Show dataset statistics

??? example "Full skill definition (Level 4)"

    Show statistics about the mined training datasets.
    
    ## Workflow
    
    ```bash
    geno-mine stats [--json]
    ```
    
    Present the results: total examples, dataset versions, breakdown by format and by skill.
