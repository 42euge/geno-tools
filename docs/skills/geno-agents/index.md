---
title: geno-agents
description: Multi-agent coordination, registration, autonomous loops
---

# geno-agents

Multi-agent coordination, registration, autonomous loops

[:material-github: GitHub](https://github.com/42euge/geno-agents){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-agents-supercharge](geno-agents-supercharge.md) | `/geno-agents-supercharge` | Run an extended autonomous work session across benchmark tasks with structured cycles of implementation, reflection, ... |
| [geno-agents-tasks-start](geno-agents-tasks-start.md) | `/geno-agents-tasks-start` | Pick up a task from the current workspace's geno-notes project scope, plan if needed, and start executing |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-agents — Agent Coordination
    
    ```!
    which geno-agents >/dev/null 2>&1 || echo "⚠️ geno-agents CLI not on PATH. Run: geno-tools install agents"
    ```
    
    You have access to geno-agents MCP tools (`list_agents`, `who`, `update_agent`, `register_agent`) and the `geno-agents` CLI on PATH (installed by geno-tools).
    
    ## Commands
    
    Parse the user's arguments to determine the action:
    
    ### `/geno-agents` (no args) or `/geno-agents status`
    Show the current agent network. Use the `list_agents` MCP tool. Display a clean summary:
    - Each agent's role, project, what they're working on, resources in use, and last seen
    - Highlight the current session
    - Flag stale agents
    
    ### `/geno-agents who`
    Show who this agent is — display the current session's agent card. Use the `who` MCP tool (no arguments needed).
    
    ### `/geno-agents who-are`
    List all other agents in the network (excludes yourself). Run:
    ```bash
    geno-agents who-are --session-id "${CLAUDE_SESSION_ID:-}"
    ```
    
    ### `/geno-agents whois <query>`
    Find agents by role or capability. Use the `whois` MCP tool.
    Example: `/geno-agents whois browser` → finds agents with browser capability.
    
    ### `/geno-agents register <role>`
    Register this session as an agent with the given role. If a `.geno-agents` file exists in the current directory, read role/description/capabilities from it instead.
    
    To register from `.geno-agents` file:
    ```bash
    geno-agents register "$(grep '^role:' .geno-agents | sed 's/^role: *//')" \
      --desc "$(grep '^description:' .geno-agents | sed 's/^description: *//')" \
      --project "$(basename $(pwd))" \
      --session-id "${CLAUDE_SESSION_ID:-}"
    ```
    
    To register with a custom role:
    Use the `register_agent` MCP tool with the provided role.
    
    After registering, confirm by showing the agent card via `list_agents`.
    
    ### `/geno-agents update`
    Update this agent's card. Parse the arguments for:
    - `--working-on "description"` — what you're currently doing
    - `--using resource` — shared resource you're using (browser, api, etc.)
    - `--status busy|available` — availability
    
    Use the `update_agent` MCP tool.
    
    ### `/geno-agents ls`
    Alias for status — list all agents.
    
    ## Auto-Registration
    
    On session start, the `geno-agents-register.sh` hook automatically registers this session using the `.geno-agents` file in the project root. If no file exists, it infers the role from `CLAUDE.md`.
    
    You can check if you're registered by running `/geno-agents status`.
    
    ## Session ID environment variable
    
    The commands above use `$CLAUDE_SESSION_ID`, which is the session identifier set by Claude Code. Other coding agents (e.g., Antigravity CLI, Cursor, Windsurf) may expose their session ID under a different environment variable. The `--session-id` flag accepts any string, so adapt the env var reference to match the agent in use. The Python CLI (`geno_agents/cli.py`) currently falls back to `CLAUDE_SESSION_ID` when no `--session-id` is provided; extending that fallback chain to other agents is tracked as a future improvement.
    
    ## `.geno-agents` File Format
    
    Projects declare their agent identity in a `.geno-agents` file at the repo root:
    
    ```yaml
    role: dev-agent
    description: Feature development and code review
    capabilities:
      - coding
      - testing
      - review
    ```
