---
title: geno-term
description: Terminal automation and session recovery
---

# geno-term

Terminal automation and session recovery

[:material-github: GitHub](https://github.com/42euge/geno-term){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-term-sessions-restart](#geno-term-sessions-restart) | `/geno-term-sessions-restart` | Restart coding agent sessions in a project tree after a crash by opening them as iTerm2 tabs and panes grouped by wor... |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-term — Claude Code Session Recovery
    
    When a macOS window server crash or accidental quit kills iTerm, Claude Code session transcripts on disk survive. This skill finds them and puts them back.
    
    ## Commands
    
    ### `/geno-term discover <dir>`
    Scan `~/.claude/projects/` for sessions whose cwd is `<dir>` or any descendant. Shows session IDs and topics grouped by cwd. Read-only.
    
    ```bash
    geno-term discover "$TARGET"
    ```
    
    ### `/geno-term restart <dir>`
    Discover sessions under `<dir>`, then open iTerm tabs — one per distinct cwd — and split each tab into panes, one per session sharing that cwd. Each pane runs `claude --resume <id>`.
    
    ```bash
    geno-term restart "$TARGET"
    ```
    
    Add `--close <name>` (repeatable) if a previous flat-tab run left old tabs around that should be closed first. Use `--print-only` to inspect the generated AppleScript.
    
    ## When to use
    
    - User reports a window server / display crash and wants prior Claude Code work back.
    - User asks what sessions were running in a project before a reboot.
    - User says "restart all my sessions in <project>".
    
    ## Layout rules
    
    One tab per distinct cwd. Pane count determines grid:
    
    - 1 session → single pane
    - 2–3 sessions → vertical strip
    - 4 sessions → 2×2
    - 5–6 sessions → 3×2
    
    More than 6 sessions sharing a cwd means multiple tabs for that cwd — the CLI handles this by splitting into chunks (future work).
    
    ## Caveats
    
    - macOS + iTerm2 only.
    - Sessions that hit a rate limit before the crash may still be limited on resume.
    - If a session already resumed earlier in the day, `claude --resume` continues the same JSONL — no fork.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-term \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = sessions discovered and listed, or iTerm tabs opened with resumed sessions
    - `failure` = geno-term CLI missing, no sessions found under target directory, or AppleScript failed
    - `abandoned` = user stopped early

## geno-term-sessions-restart

**Slash command:** `/geno-term-sessions-restart`
  **Arguments:** `"<target_dir>"`

> Restart coding agent sessions in a project tree after a crash by opening them as iTerm2 tabs and panes grouped by wor...

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — the target directory. Defaults to the current working directory if empty.

??? example "Full skill definition (Level 4)"

    Recover coding agent sessions in a project tree after a crash by restarting them as iTerm2 tabs+panes grouped by cwd.
    
    ## Input
    
    `$ARGUMENTS` — the target directory. Defaults to the current working directory if empty.
    
    ## Steps
    
    1. Resolve `$ARGUMENTS` (or `pwd`) to an absolute path.
    2. Run `geno-term discover "<path>"` and show the user the grouped list.
    3. Ask before restarting if more than 8 sessions would open.
    4. Run `geno-term restart "<path>"`.
    5. Report the number of tabs and panes opened.
