---
title: geno-specs
description: Execution specifications — create, validate, run, and review
---

# geno-specs

Execution specifications — create, validate, run, and review

[:material-github: GitHub](https://github.com/42euge/geno-specs){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-specs-create](#geno-specs-create) | `/geno-specs-create` | Create a new structured execution spec |
| [geno-specs-list](#geno-specs-list) | `/geno-specs-list` | List specs with optional status and tag filters |
| [geno-specs-run](#geno-specs-run) | `/geno-specs-run` | Pick up a spec, render its agent prompt, and execute it |
| [geno-specs-show](#geno-specs-show) | `/geno-specs-show` | Show a spec's full contents, as JSON, or as an agent-executable prompt |
| [geno-specs-validate](#geno-specs-validate) | `/geno-specs-validate` | Run a spec's completion checks |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-specs — Execution Specs for Agents
    
    Create, manage, and execute structured specs that agents (`/geno-agents`) or dev loops (`/geno-dev`) can pick up and run autonomously. Specs go beyond tasks — they define inputs, outputs, steps, and machine-checkable validation criteria.
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-specs-create [title]` | Create a new spec (interactive or from template) |
    | `/geno-specs-run [spec-id]` | Pick up a spec, render its agent prompt, and execute it |
    | `/geno-specs-list` | List specs with optional status/tag filters |
    | `/geno-specs-show [spec-id]` | Show a spec's full contents or render as agent prompt |
    | `/geno-specs-validate [spec-id]` | Run a spec's completion checks (output existence, commands) |
    
    ## Spec Lifecycle
    
    ```
    draft → ready → running → done
                           → failed → ready (retry)
    Any state → abandoned
    ```
    
    ## Spec Format
    
    YAML frontmatter + markdown body. Frontmatter carries machine-readable metadata (inputs, outputs, checks, agent requirements). Body carries human/agent-readable instructions (context, steps, acceptance criteria).
    
    ## Integration
    
    - **geno-notes**: Specs can reference geno-notes tasks. A spec is the execution blueprint; a task is the tracking item.
    - **geno-agents**: Agents pick up `ready` specs via `geno-specs list --status ready --json` and execute them.
    - **geno-dev**: Dev loops iterate over specs via `geno-specs run <id>` which renders the agent prompt.
    
    ## Runtime
    
    Python CLI: `geno-specs` (installed via pipx or editable install).

## geno-specs-create

**Slash command:** `/geno-specs-create`

> Create a new structured execution spec

??? info "Observability"

    success_signal: "spec file created and populated with inputs/outputs/steps" failure_signals: - "geno-specs create command failed" - "scope directory could not be initialized" - "user abandoned spec before filling required fields" knowledge_reads: - "available templates (geno-specs create --list-templates)" - "existing specs in scope (project or global)" knowledge_writes: - "spec file (YAML frontmatter + markdown body)" - "scope directory initialized (./geno/geno-specs/ or ~/.geno/geno-specs/)"

??? example "Full skill definition (Level 4)"

    Create a structured execution blueprint that agents or dev loops can execute autonomously.
    
    ## Input
    
    `$ARGUMENTS` is optional. Formats:
    - `title words here` — create a spec with that title
    - `template:bug-fix Title here` — use a template
    - (empty) — interactive mode
    
    ## Workflow
    
    ### 1. Determine scope
    
    Check if a project scope exists (`./geno/geno-specs/`). If not, ask the user:
    - Initialize project scope here
    - Use global scope (`~/.geno/geno-specs/`)
    
    ### 2. Parse arguments
    
    If `$ARGUMENTS` starts with `template:`, extract the template name and remaining title.
    
    If no arguments, use `AskUserQuestion` to gather:
    - Title (required)
    - Template (optional — show available templates)
    - Tags (optional)
    
    ### 3. Create the spec file
    
    Run:
    ```bash
    geno-specs create "Title" [--template name] [--tag tag1 --tag tag2]
    ```
    
    ### 4. Fill in the spec
    
    Read the created spec file. Then help the user fill in the key sections interactively:
    
    1. **Context** — what problem this solves, background information
    2. **Inputs** — files the agent needs to read
    3. **Steps** — ordered execution steps (templates pre-fill these)
    4. **Outputs** — files that should exist/change when done
    5. **Checks** — commands to validate completion (e.g., `pytest`, `ruff check`)
    6. **Acceptance criteria** — human-readable done conditions
    7. **Agent requirements** — capabilities needed, preferred model
    
    Use `geno-specs edit <id>` to add each piece:
    ```bash
    geno-specs edit <id> --add-input "src/auth.py:Current auth module"
    geno-specs edit <id> --add-output "src/auth.py:contains TokenRefresher"
    geno-specs edit <id> --add-check "pytest tests/:exit 0"
    geno-specs edit <id> --add-step "Implement the refresh logic"
    geno-specs edit <id> --agent-cap python --agent-cap api
    ```
    
    Or edit the markdown file directly — it's YAML frontmatter + markdown body.
    
    ### 5. Mark ready (optional)
    
    Ask if the spec is complete. If yes:
    ```bash
    geno-specs ready <id>
    ```
    
    ### 6. Report
    
    Show the final spec and its file path. Suggest next steps:
    - `geno-specs show <id> --prompt` to preview the agent prompt
    - `geno-specs run <id>` to execute
    - Edit the file directly for fine-tuning
    
    ## Available Templates
    
    | Template | Use case |
    |---|---|
    | `bug-fix` | Fix a bug: reproduce, root-cause, patch, verify |
    | `feature` | Add a new feature end-to-end |
    | `refactor` | Restructure code without changing behavior |
    | `migration` | Data, schema, or API migration |
    | `test` | Add or improve test coverage |
    | `review` | Code review with structured feedback |
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-specs-create \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --scope project \
      --produced "<path to created spec file>"
    ```
    
    - `success` = spec file created with populated frontmatter and body sections
    - `failure` = spec creation command failed or scope could not be initialized
    - `abandoned` = user cancelled before completing required fields

## geno-specs-list

**Slash command:** `/geno-specs-list`

> List specs with optional status and tag filters

??? info "Observability"

    success_signal: "spec listing displayed (or empty list with suggestion)" failure_signals: - "geno-specs list command failed" - "no scope directory found" knowledge_reads: - "spec files in active scope (project or global)" knowledge_writes: []

??? example "Full skill definition (Level 4)"

    Show all specs in the active scope with optional filters.
    
    ## Input
    
    `$ARGUMENTS` can contain filter flags:
    - `--status <status>` or just `ready`, `draft`, `running`, `done`, `failed`
    - `--tag <tag>`
    - `--json` for machine-readable output
    
    ## Workflow
    
    Parse `$ARGUMENTS` for any filters, then run:
    
    ```bash
    geno-specs list [--status STATUS] [--tag TAG] [--json]
    ```
    
    Display the results. If the list is empty, suggest creating a spec with `/geno-specs-create`.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-specs-list \
      --status <success|failure> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --scope project
    ```
    
    - `success` = spec listing displayed (including empty lists with suggestion)
    - `failure` = list command failed or no scope directory found

## geno-specs-run

**Slash command:** `/geno-specs-run`

> Pick up a spec, render its agent prompt, and execute it

??? info "Observability"

    success_signal: "spec executed and all validation checks passed, marked done" failure_signals: - "validation checks failed after execution" - "dependency specs not in done state" - "spec marked failed after unrecoverable error" knowledge_reads: - "spec file (inputs, steps, outputs, checks)" - "dependency specs (depends_on entries)" - "input files listed in the spec" knowledge_writes: - "output files listed in the spec" - "spec status transition (ready → running → done/failed)"

??? example "Full skill definition (Level 4)"

    Pick up a `ready` spec and execute it as the current agent.
    
    ## Input
    
    `$ARGUMENTS` is the spec ID or a fuzzy pattern. If empty, show ready specs and ask which to run.
    
    ## Workflow
    
    ### 1. Select the spec
    
    If `$ARGUMENTS` is provided:
    ```bash
    geno-specs show "$ARGUMENTS" --json
    ```
    
    If empty, list ready specs:
    ```bash
    geno-specs list --status ready --json
    ```
    Then use `AskUserQuestion` to let the user pick one.
    
    ### 2. Check dependencies
    
    If the spec has `depends_on` entries, verify those specs are `done`:
    ```bash
    geno-specs show <dep-id> --json
    ```
    If any dependency is not done, warn the user and ask whether to proceed anyway.
    
    ### 3. Transition to running
    
    ```bash
    geno-specs run <spec-id>
    ```
    
    This prints the rendered agent prompt. Read it to understand the full task.
    
    ### 4. Execute
    
    Work through the spec's steps:
    1. Read the input files listed in the spec
    2. Follow the steps in order
    3. Create/modify the output files as specified
    4. After each major step, check if the acceptance criteria are being met
    
    ### 5. Validate
    
    When you believe the work is complete, run validation:
    ```bash
    geno-specs validate <spec-id>
    ```
    
    Review the results. If all checks pass, mark done:
    ```bash
    geno-specs done <spec-id>
    ```
    
    If checks fail, fix the issues and re-validate. If the spec cannot be completed, mark failed:
    ```bash
    geno-specs fail <spec-id>
    ```
    
    ### 6. Report
    
    Summarize what was done, what passed, and any issues encountered.
    
    ## Loop Integration
    
    When called from a `/geno-dev` loop or `/geno-agents` supercharge cycle, this skill can process multiple specs in sequence. The loop driver selects specs via `geno-specs list --status ready --json` and calls this skill for each.
    
    ## Completion
    
    When this skill finishes (success, failure, or abandoned), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-specs-run \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --scope project \
      --produced "<list of output files created/modified>"
    ```
    
    - `success` = spec executed, all validation checks passed, marked done
    - `failure` = validation checks failed after execution or spec marked failed
    - `abandoned` = user stopped execution before completion or dependency check blocked

## geno-specs-show

**Slash command:** `/geno-specs-show`

> Show a spec's full contents, as JSON, or as an agent-executable prompt

??? info "Observability"

    success_signal: "spec contents displayed in requested format" failure_signals: - "spec ID not found or ambiguous" - "geno-specs show command failed" knowledge_reads: - "spec file (YAML frontmatter + markdown body)" knowledge_writes: []

??? example "Full skill definition (Level 4)"

    Display a spec's contents in the requested format.
    
    ## Input
    
    `$ARGUMENTS` is the spec ID, optionally followed by `--prompt` or `--json`.
    
    ## Workflow
    
    ```bash
    geno-specs show <spec-id> [--prompt] [--json]
    ```
    
    - Default: show the raw spec file (YAML frontmatter + markdown body)
    - `--prompt`: render as a self-contained agent prompt (what an agent would receive)
    - `--json`: structured JSON for machine consumption
    
    ## Completion
    
    When this skill finishes (success or failure), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-specs-show \
      --status <success|failure> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --scope project
    ```
    
    - `success` = spec contents displayed in the requested format
    - `failure` = spec ID not found, ambiguous match, or show command failed

## geno-specs-validate

**Slash command:** `/geno-specs-validate`

> Run a spec's completion checks

??? info "Observability"

    success_signal: "all output checks and validation commands passed" failure_signals: - "one or more output checks failed" - "validation command returned non-zero exit code" - "spec ID not found" knowledge_reads: - "spec file (outputs and checks definitions)" - "output files referenced by the spec" knowledge_writes: - "spec status transition (running → done, if all checks pass and user confirms)"

??? example "Full skill definition (Level 4)"

    Check whether a spec's completion criteria are met.
    
    ## Input
    
    `$ARGUMENTS` is the spec ID.
    
    ## Workflow
    
    ```bash
    geno-specs validate <spec-id>
    ```
    
    This runs two categories of checks:
    
    1. **Output checks** — verify expected output files exist and satisfy their content checks (e.g., `contains "class Foo"`)
    2. **Validation commands** — run shell commands and check exit codes (e.g., `pytest` → exit 0)
    
    Report results. If all pass and the spec is in `running` status, suggest marking it done:
    ```bash
    geno-specs done <spec-id>
    ```
    
    ## Completion
    
    When this skill finishes (success or failure), emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-specs-validate \
      --status <success|failure> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors> \
      --scope project
    ```
    
    - `success` = all output checks and validation commands passed
    - `failure` = one or more checks failed or spec ID not found
