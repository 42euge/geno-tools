---
title: geno-notes
description: Project journal — tasks, timestamped journal entries, plans with two-scope (global + per-project) storage.
---

# geno-notes

Project journal — tasks, timestamped journal entries, plans with two-scope (global + per-project) storage.

[:material-github: GitHub](https://github.com/42euge/geno-notes){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-notes-sites-generate](#geno-notes-sites-generate) | `/geno-notes-sites-generate` | Generate a MkDocs Material website from geno-notes content. Builds tasks, journal entries, wiki p... |
| [geno-notes-wiki-compile](#geno-notes-wiki-compile) | `/geno-notes-wiki-compile` | Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern. |
| [geno-notes-wiki-lint](#geno-notes-wiki-lint) | `/geno-notes-wiki-lint` | Health-check the wiki against primary sources. Detect stale pages, orphans, missing pages, contra... |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-notes — Project Journal
    
    Persistent, greppable, concurrent-safe project journal. One file per task,
    chunked journal files, and two coexisting storage scopes.
    
    ## Available skills
    
    | Skill | Slash command | Description |
    |-------|--------------|-------------|
    | geno-notes | /gt-notes | Manage tasks, journal entries, plans across global and project scopes |
    | geno-notes-wiki-compile | /geno-notes-wiki-compile | Compile primary sources into wiki pages |
    | geno-notes-wiki-lint | /geno-notes-wiki-lint | Health-check the wiki against primary sources |
    | geno-notes-sites-generate | /geno-notes-sites-generate | Generate a MkDocs Material website from notes |

## geno-notes-sites-generate

**Slash command:** `/geno-notes-sites-generate`
  **Arguments:** `[--serve] [--open] [--port PORT] [--all] [--global|--project]`

> Generate a MkDocs Material website from geno-notes content. Builds tasks, journal entries, wiki pages, and plans into a browsable static site.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes site`.

??? example "Full skill definition (Level 4)"

    # Generate Site
    
    Generate a MkDocs Material website from the notes in the active scope. The site is built to `.geno-notes/_site_staging/site/` (never checked in).
    
    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes site`.
    
    ## Options
    
    | Flag | Effect |
    |------|--------|
    | `--open` | Build and open the site in the default browser |
    | `--serve` | Start `mkdocs serve` for live-reloading preview |
    | `--port PORT` | Port for serve mode (default 8000) |
    | `--all` | Merge project + global scopes into one site |
    | `--global` | Force global scope |
    | `--project` | Force project scope |
    
    Default behavior (no flags): build, then ask the user if they want to open.
    
    ## Examples
    
    ```bash
    geno-notes site --open
    geno-notes site --serve --all
    geno-notes site --serve --port 3000 --project
    ```
    
    ## What it builds
    
    The site generator stages content from the active scope(s) into a temporary MkDocs project:
    
    - **Tasks** — grouped by status (active, backlog, done, abandoned)
    - **Journal** — monthly entries rendered as timeline pages
    - **Wiki** — compiled topic pages with wikilinks
    - **Plans** — task-linked planning documents
    
    ## Dependencies
    
    Requires `mkdocs` and `mkdocs-material`. The CLI will prompt to install them if missing.

## geno-notes-wiki-compile

**Slash command:** `/geno-notes-wiki-compile`
  **Arguments:** `[--global|--project]`

> Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes compile`.

??? example "Full skill definition (Level 4)"

    # Wiki Compile
    
    Compile primary sources into wiki pages (Karpathy llm-wiki pattern).
    
    The primary sources (tasks, journal, plans) are the system of record. The wiki is a **derived view** — a persistent, compounding synthesis that can always be rebuilt from the primaries.
    
    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes compile`.
    
    ## Options
    
    | Flag | Effect |
    |------|--------|
    | `--global` | Force global scope |
    | `--project` | Force project scope |
    
    ## Workflow
    
    1. Run `geno-notes compile` — this dumps all source material AND existing wiki pages.
    2. Read the output. Identify distinct topics, entities, themes, and connections across the sources.
    3. For each topic, either **update an existing wiki page** or **create a new one**:
       - Write to `<scope-dir>/wiki/<topic-slug>.md`
       - Use `[[page-name]]` wikilinks to connect related pages
       - Cite source tasks by ID (e.g. `(task: 20260425-auth-flow)`) and journal entries by date
       - Include YAML frontmatter: `tags`, `sources` (list of task IDs / journal months referenced), `updated` (ISO date)
    4. Update `<scope-dir>/wiki/index.md` — a catalog of every wiki page with a link and one-line summary, organized by category.
    5. Log the compile: `geno-notes note "wiki compile: N pages created, M updated" --kind milestone`
    
    ## Page guidelines
    
    - Each page covers one distinct topic, entity, or concept
    - Pages should be self-contained but link to related pages
    - Prefer updating over creating — the wiki compounds over time
    - When sources contradict, note the contradiction and cite both sides
    - Status-aware: reflect task statuses (done = resolved, active = in progress, abandoned = dropped)
    
    ## Examples
    
    ```bash
    geno-notes compile
    geno-notes compile --global
    geno-notes compile --project
    ```

## geno-notes-wiki-lint

**Slash command:** `/geno-notes-wiki-lint`
  **Arguments:** `[--global|--project]`

> Health-check the wiki against primary sources. Detect stale pages, orphans, missing pages, contradictions, and dead references, then fix them.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes lint`.

??? example "Full skill definition (Level 4)"

    # Wiki Lint
    
    Health-check the wiki against primary sources.
    
    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes lint`.
    
    ## Options
    
    | Flag | Effect |
    |------|--------|
    | `--global` | Force global scope |
    | `--project` | Force project scope |
    
    ## Workflow
    
    1. Run `geno-notes lint` — this dumps existing wiki pages AND all source material.
    2. Read the output. Check for:
       - **Stale pages** — wiki claims that newer tasks/journal entries have superseded
       - **Orphan pages** — wiki pages with no inbound wikilinks from other pages
       - **Missing pages** — topics referenced via `[[wikilink]]` but no page exists
       - **Gaps** — important topics in the sources that have no wiki page yet
       - **Contradictions** — wiki pages that conflict with each other or with source material
       - **Dead references** — citations to task IDs or journal entries that no longer exist
    3. Report findings as a checklist. For each issue, state what's wrong and suggest a fix.
    4. If the user approves, apply fixes directly (update/create/delete wiki pages).
    5. Log the lint: `geno-notes note "wiki lint: N issues found, M fixed" --kind milestone`
    
    ## Examples
    
    ```bash
    geno-notes lint
    geno-notes lint --global
    geno-notes lint --project
    ```
