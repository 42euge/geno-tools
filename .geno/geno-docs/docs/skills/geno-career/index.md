---
title: geno-career
description: Career toolkit — job search, resume building, application tracking
---

# geno-career

Career toolkit — job search, resume building, application tracking

[:material-github: GitHub](https://github.com/42euge/geno-career){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-career-applications-track](geno-career-applications-track.md) | `/geno-career-applications-track` | Track job applications through the pipeline |
| [geno-career-jobs-search](geno-career-jobs-search.md) | `/geno-career-jobs-search` | Search for job postings across multiple boards (LinkedIn, Indeed, Glassdoor, Wellfound, YC) |
| [geno-career-letters-generate](geno-career-letters-generate.md) | `/geno-career-letters-generate` | Generate a tailored cover letter for a specific job posting |
| [geno-career-resumes-build](geno-career-resumes-build.md) | `/geno-career-resumes-build` | Build or tailor a resume for a specific job posting |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-career
    
    Career management skills for AI coding agents. Search job boards, tailor resumes to
    specific postings, generate cover letters, and track application status through
    the pipeline.
    
    Installed via [geno-tools](https://github.com/42euge/geno-tools):
    
    ```bash
    geno-tools install career
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/gt-career-jobs-search <query>` | Search job boards for matching positions |
    | `/gt-career-resumes-build <job-url-or-desc>` | Tailor a resume for a specific job posting |
    | `/gt-career-letters-generate <job-url-or-desc>` | Generate a cover letter for a specific role |
    | `/gt-career-applications-track [add\|update\|list\|show]` | Track and manage job applications |
    
    ## Configuration
    
    User config lives at `~/.geno-tools/geno-career/configs/career.yaml`. Set your
    profile info, preferred job boards, resume paths, and output directories.
    
    ## Data
    
    Application tracking and generated documents default to `~/Documents/career/`.
