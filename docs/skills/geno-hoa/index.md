---
title: geno-hoa
description: HOA portal automation
---

# geno-hoa

HOA portal automation

[:material-github: GitHub](https://github.com/42euge/geno-hoa){ .md-button }

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-hoa
    
    HOA portal automation skills for Claude Code. Navigates HOA management portals (MyGreenCondo, AppFolio, BuildingLink, etc.) via browser automation to download documents, check account status, and extract financial data for tax prep or remodel projects.
    
    **Local-only skillset.** HOA account data is sensitive; this repo is not published.
    
    ```bash
    geno-tools install /path/to/geno-hoa
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-hoa-login` | Navigate to HOA portal, ensure authenticated, save config |
    | `/geno-hoa-docs [category]` | Browse and download documents from the portal's document library |
    | `/geno-hoa-account` | Show account status — balance, dues, violations, recent payments |
    | `/geno-hoa-dues [year]` | Extract annual HOA dues paid for tax deduction (Schedule E) |
    
    ## Data Storage
    
    All HOA data is stored under `~/docs/home/hoa/`:
    - `hoa-config.yaml` — portal URL, unit info, portal type
    - `documents/` — downloaded PDFs/docs organized by category
    - `account-history/` — payment and assessment records
    
    ## Runtime
    
    No venv or scripts — all commands are pure markdown workflows. Browser automation commands depend on the `geno-vla` MCP server being registered in Claude.
    
    ## Integration
    
    - **geno-taxes**: `/geno-hoa-dues 2024` outputs annual dues total for Schedule E line items
    - **geno-remodel**: `/geno-hoa-docs insurance` fetches the COI and rules docs needed for alteration applications
