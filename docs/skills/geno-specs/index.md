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
| [geno-specs-create](geno-specs-create.md) | `/geno-specs-create` | Create a new structured execution spec |
| [geno-specs-list](geno-specs-list.md) | `/geno-specs-list` | List specs with optional status and tag filters |
| [geno-specs-run](geno-specs-run.md) | `/geno-specs-run` | Pick up a spec, render its agent prompt, and execute it |
| [geno-specs-show](geno-specs-show.md) | `/geno-specs-show` | Show a spec's full contents, as JSON, or as an agent-executable prompt |
| [geno-specs-validate](geno-specs-validate.md) | `/geno-specs-validate` | Run a spec's completion checks |

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
