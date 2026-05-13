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
| [geno-career-applications-track](#geno-career-applications-track) | `/geno-career-applications-track` | Track job applications through the pipeline |
| [geno-career-jobs-search](#geno-career-jobs-search) | `/geno-career-jobs-search` | Search for job postings across multiple boards (LinkedIn, Indeed, Glassdoor, Wellfound, YC) |
| [geno-career-letters-generate](#geno-career-letters-generate) | `/geno-career-letters-generate` | Generate a tailored cover letter for a specific job posting |
| [geno-career-resumes-build](#geno-career-resumes-build) | `/geno-career-resumes-build` | Build or tailor a resume for a specific job posting |

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

## geno-career-applications-track

**Slash command:** `/geno-career-applications-track`
  **Arguments:** `"[add|update|list|show|stats] [args...]"`

> Track job applications through the pipeline

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — Subcommand + args:
    - `add <company> <role> [--url <url>] [--status applied]` — Add new application
    - `update <id-or-company> --status <status> [--notes "..."]` — Update status
    - `list [--status <status>] [--active]` — List applications
    - `show <id-or-company>` — Show full details for an application
    - `stats` — Summary statistics across all applications
    - (no args) — Show active applications (same as `list --active`)

??? example "Full skill definition (Level 4)"

    Track job applications through the hiring pipeline. Maintains a YAML file with
    all applications, their current status, key dates, and associated documents.
    
    ## Input
    
    `$ARGUMENTS` — Subcommand + args:
    - `add <company> <role> [--url <url>] [--status applied]` — Add new application
    - `update <id-or-company> --status <status> [--notes "..."]` — Update status
    - `list [--status <status>] [--active]` — List applications
    - `show <id-or-company>` — Show full details for an application
    - `stats` — Summary statistics across all applications
    - (no args) — Show active applications (same as `list --active`)
    
    ## Data Format
    
    Applications are stored in a YAML file at `data/applications.yaml` (repo root, gitignored):
    
    ```yaml
    applications:
      - id: 1
        company: Stripe
        role: Senior Backend Engineer
        url: https://stripe.com/jobs/...
        status: technical
        applied_date: 2026-04-20
        status_history:
          - { status: applied, date: 2026-04-20 }
          - { status: phone-screen, date: 2026-04-23 }
          - { status: technical, date: 2026-04-25, notes: "Take-home due May 1" }
        resume_path: ~/Documents/career/resumes/resume-stripe-senior-backend.md
        cover_letter_path: ~/Documents/career/cover-letters/cover-letter-stripe-senior-backend.md
        contacts:
          - { name: "Jane Doe", role: "Hiring Manager", email: "jane@stripe.com" }
        salary_range: "$180k-$220k"
        notes: "Referral from Alex. Team works on payment processing infra."
        tags: [fintech, backend, distributed-systems]
    ```
    
    ## Workflow
    
    ### `add`
    
    1. Create the tracker file if it doesn't exist
    2. Auto-increment the ID
    3. Set `applied_date` to today, `status` to the provided value (default: `applied`)
    4. Initialize `status_history` with the first entry
    5. If resume/cover-letter paths exist for this company in the output dirs, link them
    6. Write to tracker file
    
    ### `update`
    
    1. Find the application by ID or fuzzy-match on company name
    2. If ambiguous, ask the user to clarify
    3. Update the status field
    4. Append to `status_history` with today's date and optional notes
    5. Write to tracker file
    
    ### `list`
    
    1. Read tracker file
    2. Filter by `--status` if provided, or `--active` (excludes rejected/withdrawn/accepted)
    3. Display as a clean table:
    
    ```
     ID | Company  | Role                    | Status       | Applied    | Days
    ----+----------+-------------------------+--------------+------------+------
      1 | Stripe   | Senior Backend Eng      | technical    | 2026-04-20 |    6
      3 | Vercel   | Staff Platform Eng      | phone-screen | 2026-04-22 |    4
      5 | Linear   | Senior Product Eng      | applied      | 2026-04-25 |    1
    ```
    
    ### `show`
    
    Display full details for a single application including status history timeline,
    linked documents, contacts, and notes.
    
    ### `stats`
    
    Summary dashboard:
    - Total applications, active, offers, rejections
    - Average time in each stage
    - Response rate (applications that progressed past "applied")
    - Pipeline funnel visualization
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-career-applications-track \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = subcommand completed -- application added, updated, listed, shown, or stats displayed
    - `failure` = tracker file malformed, application not found, or write failed
    - `abandoned` = user stopped early or cancelled operation

## geno-career-jobs-search

**Slash command:** `/geno-career-jobs-search`
  **Arguments:** `"<query> [--remote] [--level senior] [--board linkedin] [--days 14]"`

> Search for job postings across multiple boards (LinkedIn, Indeed, Glassdoor, Wellfound, YC)

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — Required. The search query plus optional filters:
    - `<query>` — Job title, keywords, or company (e.g., "ML engineer", "senior backend at Stripe")
    - `--remote` — Filter to remote positions
    - `--level <level>` — Experience level: junior, mid, senior, staff, principal
    - `--board <board>` — Specific board: linkedin, indeed, glassdoor, wellfound, ycombinator
    - `--days <n>` — Posted within last N days (default: 30)
    - `--location <loc>` — Location filter (e.g., "San Francisco", "US")

??? example "Full skill definition (Level 4)"

    Search for job postings matching the user's criteria. Uses web search to find
    current openings across job boards.
    
    ## Input
    
    `$ARGUMENTS` — Required. The search query plus optional filters:
    - `<query>` — Job title, keywords, or company (e.g., "ML engineer", "senior backend at Stripe")
    - `--remote` — Filter to remote positions
    - `--level <level>` — Experience level: junior, mid, senior, staff, principal
    - `--board <board>` — Specific board: linkedin, indeed, glassdoor, wellfound, ycombinator
    - `--days <n>` — Posted within last N days (default: 30)
    - `--location <loc>` — Location filter (e.g., "San Francisco", "US")
    
    ## Workflow
    
    ### 1. Load config and profile
    
    Read `config/defaults/career.yaml` for default search preferences and
    `data/profile.yaml` for skills keywords (used to highlight strong matches).
    Merge with any flags from `$ARGUMENTS` (flags override config).
    
    ### 2. Build search queries
    
    For each target job board, construct a site-scoped web search query:
    - LinkedIn: `site:linkedin.com/jobs "<query>" <location> <level>`
    - Indeed: `site:indeed.com "<query>" <filters>`
    - Glassdoor: `site:glassdoor.com/Job "<query>"`
    - Wellfound: `site:wellfound.com/role "<query>"`
    - Y Combinator: `site:workatastartup.com "<query>"` or `site:ycombinator.com/jobs "<query>"`
    
    If `--board` is specified, only search that board. Otherwise search all configured boards.
    
    ### 3. Search and collect results
    
    Use `WebSearch` for each board query. For the top results, use `WebFetch` to
    extract key details:
    - Job title
    - Company name
    - Location / Remote status
    - Posted date
    - Salary range (if listed)
    - URL
    
    ### 4. Present results
    
    Display results in a clean table, grouped by board. Include a summary count
    and highlight strong matches based on the user's profile keywords from config.
    
    ### 5. Offer next steps
    
    After presenting results, offer:
    - "Want me to tailor your resume for any of these?" → `/gt-career-resumes-build`
    - "Want me to write a cover letter?" → `/gt-career-letters-generate`
    - "Want me to add any to your tracker?" → `/gt-career-applications-track add`
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-career-jobs-search \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = results table displayed with at least one matching posting
    - `failure` = all search queries returned zero results, config missing, or tool calls failed
    - `abandoned` = user stopped early or cancelled search

## geno-career-letters-generate

**Slash command:** `/geno-career-letters-generate`
  **Arguments:** `"<job-url-or-description> [--tone professional|conversational|enthusiastic] [--resume path]"`

> Generate a tailored cover letter for a specific job posting

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — Required. Either:
    - A URL to a job posting
    - A pasted job description
    - A company name + role (e.g., "Stripe senior backend engineer")
    
    Optional flags:
    - `--tone <tone>` — Writing style: `professional` (default), `conversational`, `enthusiastic`
    - `--resume <path>` — Path to tailored resume (for consistency)
    - `--output <path>` — Custom output path

??? example "Full skill definition (Level 4)"

    Generate a tailored cover letter for a specific job posting. Researches the
    company and role, then writes a compelling letter that connects the user's
    experience to the position.
    
    ## Input
    
    `$ARGUMENTS` — Required. Either:
    - A URL to a job posting
    - A pasted job description
    - A company name + role (e.g., "Stripe senior backend engineer")
    
    Optional flags:
    - `--tone <tone>` — Writing style: `professional` (default), `conversational`, `enthusiastic`
    - `--resume <path>` — Path to tailored resume (for consistency)
    - `--output <path>` — Custom output path
    
    ## Workflow
    
    ### 1. Load context
    
    Read from the `data/` directory at the repo root:
    - `data/profile.yaml` for contact info and skills inventory
    - `data/resumes/base.md` for experience context
    - Config `config/defaults/career.yaml` for tone preference
    
    If `--resume` provided, read that instead of the base resume.
    
    ### 2. Extract job details
    
    If URL provided, `WebFetch` the posting. Extract:
    - Role title and team
    - Key responsibilities
    - Required and preferred qualifications
    - Company mission/values (from posting or company page)
    
    ### 3. Research company (optional)
    
    Use `WebSearch` to gather:
    - Recent company news, funding, product launches
    - Company culture signals (blog posts, engineering blog)
    - Notable projects or tech stack
    
    Keep this brief — 2-3 relevant facts max for the letter.
    
    ### 4. Generate cover letter
    
    Write a cover letter that:
    - Opens with genuine interest in the specific role (not generic)
    - Connects 2-3 pieces of the user's experience to key requirements
    - References something specific about the company (from research)
    - Demonstrates understanding of the role's challenges
    - Closes with enthusiasm and a clear call to action
    - Matches the requested tone
    - Stays under one page (~300-400 words)
    
    **Rules:**
    - Never use filler phrases ("I am writing to express my interest...")
    - Never claim skills or experience the user doesn't have
    - Be specific — generic letters are worse than no letter
    - Match the company's communication style (startup casual vs. enterprise formal)
    
    ### 5. Write output
    
    Save to:
    1. `--output` path if provided
    2. `data/generated/cover-letters/cover-letter-{company}-{role-slug}.md`
    
    ### 6. Offer next steps
    
    - "Want me to adjust the tone or emphasis?"
    - "Want me to add this to your application tracker?" → `/gt-career-applications-track add`
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-career-letters-generate \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = cover letter written to output path and displayed to user
    - `failure` = job posting unreachable, profile/resume missing, or write failed
    - `abandoned` = user stopped early or cancelled generation

## geno-career-resumes-build

**Slash command:** `/geno-career-resumes-build`
  **Arguments:** `"<job-url-or-description> [--base path/to/resume.md] [--format md|pdf]"`

> Build or tailor a resume for a specific job posting

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — Required. Either:
    - A URL to a job posting
    - A pasted job description
    - A path to a file containing the job description
    
    Optional flags:
    - `--base <path>` — Path to base resume (overrides config)
    - `--format <fmt>` — Output format: `md` (default), `pdf` (requires pandoc + LaTeX)
    - `--output <path>` — Custom output path

??? example "Full skill definition (Level 4)"

    Tailor a resume to match a specific job posting. Analyzes the posting's requirements
    and reshapes the user's base resume to emphasize relevant skills and experience.
    
    ## Input
    
    `$ARGUMENTS` — Required. Either:
    - A URL to a job posting
    - A pasted job description
    - A path to a file containing the job description
    
    Optional flags:
    - `--base <path>` — Path to base resume (overrides config)
    - `--format <fmt>` — Output format: `md` (default), `pdf` (requires pandoc + LaTeX)
    - `--output <path>` — Custom output path
    
    ## Workflow
    
    ### 1. Load base resume and profile
    
    Read from the `data/` directory at the repo root:
    1. `--base` flag if provided
    2. Otherwise `data/resumes/base.md` (the master resume)
    3. Always also read `data/profile.yaml` for structured skills/education data
    4. Check `data/source/` for variant notes that may inform tailoring strategy
    
    If `data/resumes/base.md` doesn't exist, ask the user to provide a resume or run setup.
    
    ### 2. Extract job requirements
    
    If `$ARGUMENTS` contains a URL, use `WebFetch` to retrieve the posting.
    Parse and extract:
    - **Required skills** — languages, frameworks, tools
    - **Preferred skills** — nice-to-haves
    - **Experience level** — years, seniority
    - **Key responsibilities** — what the role does day-to-day
    - **Company context** — domain, stage, team size
    
    ### 3. Analyze gaps and strengths
    
    Compare the job requirements against the base resume:
    - **Strong matches** — experience that directly maps to requirements
    - **Reframeable experience** — adjacent skills that can be positioned to match
    - **Gaps** — requirements not covered (flag but don't fabricate)
    
    ### 4. Generate tailored resume
    
    Restructure the resume:
    - Reorder sections to lead with most relevant experience
    - Rewrite bullet points to use keywords from the posting
    - Emphasize quantified achievements that map to responsibilities
    - Adjust the summary/objective to target this specific role
    - Keep it honest — never fabricate experience or skills
    
    ### 5. Write output
    
    Save the tailored resume to:
    1. `--output` path if provided
    2. `data/generated/resumes/resume-{company}-{role-slug}.md`
    
    Display a diff summary showing what changed from the base resume.
    
    ### 6. Offer next steps
    
    - "Want me to generate a cover letter for this role?" → `/gt-career-letters-generate`
    - "Want me to add this to your application tracker?" → `/gt-career-applications-track add`
    - "Want me to export to PDF?" (if format was md)
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-career-resumes-build \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = tailored resume written to output path with diff summary displayed
    - `failure` = base resume missing, job posting unreachable, or write failed
    - `abandoned` = user stopped early or cancelled tailoring
