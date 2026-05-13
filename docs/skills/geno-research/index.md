---
title: geno-research
description: Research wiki, paper generation, repo docs
---

# geno-research

Research wiki, paper generation, repo docs

[:material-github: GitHub](https://github.com/42euge/geno-research){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-research
    
    Research skills for Claude Code. Maintains an evolving, cross-referenced knowledge base using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
    
    Installed via [geno-tools](https://github.com/42euge/geno-tools):
    ```bash
    geno-tools install research
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/gt-research <topic>` | Research a topic and build/update a wiki of linked markdown notes |
    | `/gt-research ingest <url-or-file>` | Ingest a source into the wiki |
    | `/gt-research lint` | Check wiki health — broken links, orphans, contradictions |
    | `/gt-research-paper-generate [focus]` | Generate an academic paper from findings |
    | `/gt-research-repo-docs [focus]` | Generate purpose-driven repo documentation |
    
    Project tasks and journal have moved out of this repo. Use [`/gt-notes`](https://github.com/42euge/geno-notes) (from the `geno-notes` repo) for task management and timestamped journal entries.
    
    ## Runtime
    
    No venv or scripts — all commands are pure markdown workflows.
