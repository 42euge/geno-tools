---
title: geno-notes
description: Project journal, task management, wiki, and site generation
---

# geno-notes

Project journal, task management, wiki, and site generation

[:material-github: GitHub](https://github.com/42euge/geno-notes){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-notes-sites-generate](#geno-notes-sites-generate) | `/geno-notes-sites-generate` | Generate a MkDocs Material website from geno-notes content |
| [geno-notes-vault-generate](#geno-notes-vault-generate) | `/geno-notes-vault-generate` | Generate an Obsidian vault from geno-notes content |
| [geno-notes-wiki-compile](#geno-notes-wiki-compile) | `/geno-notes-wiki-compile` | Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern |
| [geno-notes-wiki-lint](#geno-notes-wiki-lint) | `/geno-notes-wiki-lint` | Health-check the wiki against primary sources |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-notes — Project Journal
    
    ```!
    command -v geno-notes >/dev/null 2>&1 || echo "⚠️ geno-notes is not installed. Run install.sh from the geno-notes repo."
    ```
    
    A persistent, greppable, concurrent-safe project journal. Replaces the legacy `geno-tools/labnotes/` layout with one file per task, chunked journal files, and two coexisting storage scopes.
    
    ## Scopes
    
    - **Global** (`~/.geno/geno-notes/`) — cross-project knowledge, personal dev log that spans repos.
    - **Project** (`./geno/geno-notes/` found by walking up from cwd) — tasks, notes, plans tied to one repo.
    
    Active scope resolves in this order:
    1. `$GENO_NOTES_SCOPE=global|project`
    2. `$GENO_NOTES_DIR=<path>`
    3. Project detected in cwd or ancestors
    4. Global (auto-created on first use)
    
    Any command takes `--global` or `--project` to override. Read commands take `--all` to union both.
    
    ## Sub-skills
    
    | Skill | Slash command | Description |
    |-------|--------------|-------------|
    | geno-notes-wiki-compile | /geno-notes-wiki-compile | Compile primary sources into wiki pages |
    | geno-notes-wiki-lint | /geno-notes-wiki-lint | Health-check the wiki against primary sources |
    | geno-notes-sites-generate | /geno-notes-sites-generate | Generate a MkDocs Material website from notes |
    
    ## Commands
    
    Parse the user's `$ARGUMENTS` and dispatch to the CLI.
    
    ### `/gt-notes` (no args) or `/gt-notes scope`
    Show the active scope + both dir paths.
    ```bash
    geno-notes scope
    ```
    
    ### `/gt-notes init [--global|--project]`
    Scaffold a scope at the right location and write `config.toml`.
    - No flag in a cwd without a project scope → creates `./geno/geno-notes/` (project).
    - `--global` → ensures `~/.geno/geno-notes/` is scaffolded.
    
    ### `/gt-notes add "<description>" [--tag infra --tag security]`
    Create a new task in Backlog. Returns the task ID.
    
    ### `/gt-notes start <pattern>`
    Move a task from Backlog → Active. Fuzzy matches on id, slug, or title (exact > prefix > substring). If multiple tasks match in the top tier, the CLI lists them and exits 1 — ask the user to disambiguate.
    
    ### `/gt-notes done <pattern>`  /  `/gt-notes abandon <pattern>`
    Complete or abandon a task. Same fuzzy-match rules.
    
    ### `/gt-notes note "<text>" [--task <pattern>] [--kind note|finding|decision|bug|milestone]`
    Append a timestamped entry to `journal/YYYY/YYYY-MM.{md,jsonl}`. If `--task` is given, also appends a backlink to the task's `## Journal refs` section.
    
    ### `/gt-notes inbox "<text>"`
    Free-floating quick capture — appends to `inbox.md`. Promote later with `triage`.
    
    ### `/gt-notes triage`
    Interactively walk inbox items, promoting each to a task or discarding.
    
    ### `/gt-notes list [--status active|backlog|done|abandoned] [--json] [--all]`
    List tasks in the active scope. `--all` unions both scopes. `--json` for programmatic use.
    
    ### `/gt-notes show <pattern> [--all]`
    Render a task file + its journal refs.
    
    ### `/gt-notes search <query> [--all]`
    Plain-text grep across tasks, journal, plans, inbox.
    
    ### `/gt-notes promote <pattern> [--to global|project]`
    Move a task (and its plan file, if any) between scopes. Useful when a project-scope task turns out to be cross-cutting.
    
    ### `/gt-notes reindex`
    Regenerate `index.md` and `tasks/_index.md`. The CLI does this automatically on every mutation, so run manually only after hand-editing a task file.
    
    ### `/gt-notes compile`
    Compile primary sources into wiki pages. See `/geno-notes-wiki-compile` for the full workflow.
    
    ### `/gt-notes site [--serve] [--open] [--port PORT]`
    Generate a MkDocs Material website from notes. See `/geno-notes-sites-generate` for the full workflow.
    
    ### `/gt-notes lint`
    Health-check the wiki against primary sources. See `/geno-notes-wiki-lint` for the full workflow.
    
    ## Architecture
    
    geno-notes implements the [Karpathy llm-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Three layers:
    
    | Layer | geno-notes | Role |
    |---|---|---|
    | **Primary sources** | `tasks/`, `journal/`, `plans/`, `inbox.md` | System of record. Human + agent edited. |
    | **Wiki** | `wiki/` | Derived view. Agent-generated, rebuildable. Compounds over time. |
    | **Schema** | `SKILL.md`, `GENO.md` | Tells the agent how to operate. |
    
    ## Files (per scope)
    
    ```
    <scope-dir>/
    ├── index.md                       # auto-gen dashboard
    ├── tasks/
    │   ├── _index.md                  # auto-gen list
    │   └── <task-id>.md               # YYYYMMDD-<slug>.md with YAML frontmatter
    ├── journal/YYYY/YYYY-MM.{md,jsonl}
    ├── plans/<task-id>.md
    ├── wiki/
    │   ├── index.md                   # catalog of all wiki pages
    │   └── <topic-slug>.md            # compiled topic/entity pages
    ├── inbox.md
    └── .geno-notes/
        ├── config.toml
        ├── events.jsonl               # audit log
        └── locks/                     # flock files
    ```
    
    Humans edit `.md`; consumers that need structured data should read `.jsonl` (journal) or call `geno-notes list --json`.

## geno-notes-sites-generate

**Slash command:** `/geno-notes-sites-generate`

> Generate a MkDocs Material website from geno-notes content

??? example "Full skill definition (Level 4)"

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

## geno-notes-vault-generate

**Slash command:** `/geno-notes-vault-generate`

> Generate an Obsidian vault from geno-notes content

??? example "Full skill definition (Level 4)"

    Generate an Obsidian vault from the notes in the active scope. The vault is created at `.geno-notes/_vault_staging/` (never checked in).
    
    ## Input
    
    `$ARGUMENTS` are passed as flags to `geno-notes vault`.
    
    ## Options
    
    | Flag | Effect |
    |------|--------|
    | `--all` | Merge project + global scopes into one vault |
    | `--global` | Force global scope |
    | `--project` | Force project scope |
    
    ## Workflow
    
    1. Run `geno-notes vault` with any scope flags from `$ARGUMENTS`. Pipe `n` to stdin to skip the interactive prompt: `echo n | geno-notes vault [flags]`
    2. Capture the vault path from the "Vault ready →" output line.
    3. Report what was generated — number of tasks, journal months, wiki pages, plans staged.
    4. Ask the user if they'd like to open the vault in Obsidian.
    5. If yes, open it: `open "obsidian://open?path=<vault-path>"`
    
    ## What it builds
    
    The vault generator stages content from the active scope(s) into an Obsidian-ready directory:
    
    - **Home.md** — Map of Content (MOC) linking to all sections
    - **Tasks/** — one file per task with frontmatter, plus `_index.md` MOC grouped by status
    - **Journal/** — monthly entries preserving the `YYYY/YYYY-MM.md` structure
    - **Wiki/** — compiled topic pages with native `[[wikilinks]]`
    - **Plans/** — task-linked planning documents
    - **Inbox.md** — quick captures
    - **.obsidian/** — vault config with graph view color groups, workspace defaults
    
    ## Obsidian features
    
    - **Graph view** — color-coded by section (Tasks=purple, Journal=teal, Wiki=orange, Plans=gray)
    - **Wikilinks** — `[[page]]` links work natively (geno-notes already uses this format)
    - **Tags** — task tags rendered as `#tag` for Obsidian tag search
    - **MOCs** — Home and Tasks index pages for navigation
    
    ## Examples
    
    ```bash
    geno-notes vault
    geno-notes vault --all
    geno-notes vault --project
    ```

## geno-notes-wiki-compile

**Slash command:** `/geno-notes-wiki-compile`

> Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern

??? example "Full skill definition (Level 4)"

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

> Health-check the wiki against primary sources

??? example "Full skill definition (Level 4)"

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
