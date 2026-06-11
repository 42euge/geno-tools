---
title: geno-taxes
description: Tax filing — document parsing, checklists, CPA packet prep
---

# geno-taxes

Tax filing — document parsing, checklists, CPA packet prep

[:material-github: GitHub](https://github.com/42euge/geno-taxes){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-tax-checklist](geno-tax-checklist.md) | `/geno-tax-checklist` | "Tax Document Checklist" |
| [geno-tax-fetch](geno-tax-fetch.md) | `/geno-tax-fetch` | Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation). |
| [geno-tax-parse](geno-tax-parse.md) | `/geno-tax-parse` | "Parse Tax Document" |
| [geno-tax-status](geno-tax-status.md) | `/geno-tax-status` | "Tax Filing Status" |
| [geno-tax-summary](geno-tax-summary.md) | `/geno-tax-summary` | "Tax Year Summary for CPA" |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-taxes
    
    Personal tax filing skills for AI coding agents. Manages the yearly cycle of collecting 1099s / W-2s / earnings reports, parsing them into YAML organizers under `~/docs/finance/taxes/`, and generating CPA-ready summaries.
    
    **Local-only skillset.** Tax data is sensitive; this repo is not published. Its `geno-tools` registry entry points at this directory's absolute path, and `install` copies it into `~/.geno-tools/geno-taxes/repo/`:
    
    ```bash
    geno-tools install taxes
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-tax-status [year]` | Show document collection and data entry status across all years |
    | `/geno-tax-checklist [year]` | List remaining documents with instructions on where to get them |
    | `/geno-tax-parse <file>` | Parse a PDF/CSV tax doc and populate the YAML organizer |
    | `/geno-tax-fetch <platform> [year]` | Download tax docs via geno-vla browser automation |
    | `/geno-tax-summary <year>` | Generate a CPA-ready markdown summary from the YAML organizer |
    
    ## Runtime
    
    No venv or scripts — all commands are pure markdown workflows. `gt-tax-fetch` depends on the `geno-vla` MCP server for browser automation.
