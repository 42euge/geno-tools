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
| [geno-mine-export](geno-mine-export.md) | `/geno-mine-export` | Export a dataset version to a directory for finetuning |
| [geno-mine-extract](geno-mine-extract.md) | `/geno-mine-extract` | Run the full session mining pipeline |
| [geno-mine-stats](geno-mine-stats.md) | `/geno-mine-stats` | Show dataset statistics |

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
