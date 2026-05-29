---
title: geno-remodel
description: Home remodel toolkit
---

# geno-remodel

Home remodel toolkit

[:material-github: GitHub](https://github.com/42euge/geno-remodel){ .md-button }

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-remodel
    
    Home remodel workflow skills for AI coding agents. Upload a photo of any room and plan a remodel through clickable menus — zero typing required. Also manages HOA document retrieval and submission, permit tracking, contractor coordination, and contractor website generation.
    
    **Local-only skillset.** This repo is not published. Install via absolute path:
    
    ```bash
    geno-tools install /path/to/geno-remodel
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-remodel-plan` | Analyze a room photo and create a remodel plan through guided menus |
    | `/geno-remodel-status` | Show status of all remodel projects and their HOA/permit status |
    | `/geno-remodel-hoa-fetch` | Log into HOA portal, find required forms and docs |
    | `/geno-remodel-hoa-submit` | Fill out and submit HOA approval request |
    | `/geno-remodel-site-init` | Collect contractor info and configure a website project |
    | `/geno-remodel-site-build` | Generate a complete static contractor website into `build/` |
    | `/geno-remodel-site-preview` | Serve the generated site locally and open in browser |
    
    ## Runtime
    
    No venv or scripts — all commands are pure markdown workflows. `geno-remodel-hoa-fetch` and `geno-remodel-hoa-submit` depend on the `geno-vla` MCP server for browser automation. The `site-*` commands generate pure HTML/CSS/JS with no build tools or dependencies.
