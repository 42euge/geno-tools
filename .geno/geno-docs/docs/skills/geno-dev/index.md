---
title: geno-dev
description: Developer utilities — commits, worktrees, workspaces, feature shipping
---

# geno-dev

Developer utilities — commits, worktrees, workspaces, feature shipping

[:material-github: GitHub](https://github.com/42euge/geno-dev){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-dev-branches-audit](geno-dev-branches-audit.md) | `/geno-dev-branches-audit` | Audit all branches across a workspace or repo |
| [geno-dev-commits-rewrite](geno-dev-commits-rewrite.md) | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage) |
| [geno-dev-feature-ship](geno-dev-feature-ship.md) | `/geno-dev-feature-ship` | End-to-end feature shipping |
| [geno-dev-issue-work](geno-dev-issue-work.md) | `/geno-dev-issue-work` | Select a GitHub issue or JIRA ticket and start working on it, with a choice of normal interactive mode or autonomous ... |
| [geno-dev-prs-check](geno-dev-prs-check.md) | `/geno-dev-prs-check` | Check open PRs for repos in the current session and show which ones may need to be closed |
| [geno-dev-scheduling-snooze](geno-dev-scheduling-snooze.md) | `/geno-dev-scheduling-snooze` | Snooze the current session |
| [geno-dev-sessions-fork](geno-dev-sessions-fork.md) | `/geno-dev-sessions-fork` | Fork an agent session |
| [geno-dev-sessions-remote](geno-dev-sessions-remote.md) | `/geno-dev-sessions-remote` | Start a Claude Code session with remote access in a workspace directory |
| [geno-dev-skills-retro](geno-dev-skills-retro.md) | `/geno-dev-skills-retro` | Meta-harness |
| [geno-dev-tasks-start](geno-dev-tasks-start.md) | `/geno-dev-tasks-start` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done |
| [geno-dev-workspaces-init](geno-dev-workspaces-init.md) | `/geno-dev-workspaces-init` | Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas |
| [geno-dev-worktrees-manage](geno-dev-worktrees-manage.md) | `/geno-dev-worktrees-manage` | Manage git worktrees |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-dev — Developer Utilities
    
    Dev and infrastructure skills for AI coding agents. Task execution, git history rewriting, worktree management, workspace creation, session forking, end-to-end feature shipping, issue-driven development, agentic loops, background monitoring, PR checking and branch auditing, scheduled snoozing, and skill retrospectives.
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/geno-dev-tasks-start [description]` | Pick up a task from lab notes, assess scope, plan if needed, execute, and mark done |
    | `/geno-dev-commits-rewrite` | Rewrite git commit history into a clean narrative (backup + soft reset + restage) |
    | `/geno-dev-worktrees-manage [list\|create\|switch\|prune]` | Manage git worktrees — list, create, switch, and prune |
    | `/geno-dev-workspaces-init [config\|list\|<text>]` | Create development workspaces from issues, tickets, repos, or ideas |
    | `/geno-dev-sessions-fork [session]` | Fork an agent session — extract context to continue in a new session |
    | `/geno-dev-feature-ship [description\|issue URL]` | End-to-end: scope, issue, branch, implement, and PR |
    | `/geno-dev-issue-work [number\|query\|URL]` | Pick a GitHub issue or JIRA ticket and work on it (normal or loop mode) |
    | `/geno-dev-loops-turbocharge [task] [--spec <file>]` | Spec-driven convergence loop — iterate until all acceptance criteria pass |
    | `/geno-dev-loops-cruise [task] [--plan <file>]` | Plan-driven sequential loop — execute a plan one step at a time |
    | `/geno-dev-loops-autopilot [task] [--watch <tests\|ci\|lint\|git\|all>]` | Background monitoring loop — watch CI, tests, lint, and git state |
    | `/geno-dev-loops-boost [task]` | Pomodoro focus loop — time-boxed work blocks with reflection |
    | `/geno-dev-loops-ignition [goal] [--blueprint <file>]` | Cold-start bootstrap loop — turn a high-level goal into a blueprint and verified first slice |
    | `/geno-dev-prs-check [repo\|--all]` | Check open PRs and flag ones that may need closing |
    | `/geno-dev-branches-audit [repo\|--all]` | Audit all branches — find ones needing PRs, ready to merge, or stale |
    | `/geno-dev-scheduling-snooze <time> [prompt]` | Snooze session until a specified time, then execute a prompt |
    | `/geno-dev-skills-retro [session] [--skill <name>]` | Meta-harness: analyze a failed session and patch the responsible skill |
    
    ## Runtime
    
    No venv or scripts — pure markdown workflows.
