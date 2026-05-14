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
| [geno-notes-sites-generate](geno-notes-sites-generate.md) | `/geno-notes-sites-generate` | Generate a MkDocs Material website from geno-notes content |
| [geno-notes-vault-generate](geno-notes-vault-generate.md) | `/geno-notes-vault-generate` | Generate an Obsidian vault from geno-notes content |
| [geno-notes-wiki-compile](geno-notes-wiki-compile.md) | `/geno-notes-wiki-compile` | Compile primary sources (tasks, journal, plans) into wiki pages using the Karpathy llm-wiki pattern |
| [geno-notes-wiki-lint](geno-notes-wiki-lint.md) | `/geno-notes-wiki-lint` | Health-check the wiki against primary sources |

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
