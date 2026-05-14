---
title: geno-iso
description: Docker containers for isolated Claude Code environments
---

# geno-iso

Docker containers for isolated Claude Code environments

[:material-github: GitHub](https://github.com/42euge/geno-iso){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-iso-containers-enter](geno-iso-containers-enter.md) | `/geno-iso-containers-enter` | Interactively enter a running geno-iso container |
| [geno-iso-containers-list](geno-iso-containers-list.md) | `/geno-iso-containers-list` | List geno-iso containers (running and stopped) |
| [geno-iso-containers-run](geno-iso-containers-run.md) | `/geno-iso-containers-run` | Spin up an isolated coding agent container with a mounted workspace |
| [geno-iso-credentials-extract](geno-iso-credentials-extract.md) | `/geno-iso-credentials-extract` | Refresh host credentials used for geno-iso container auth |
| [geno-iso-dev-guide](geno-iso-dev-guide.md) | `/geno-iso-dev-guide` | Development guide for the geno-iso codebase |
| [geno-iso-images-build](geno-iso-images-build.md) | `/geno-iso-images-build` | Build or rebuild the geno-iso Docker image |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-iso -- Isolated Containers for Coding Agents
    
    Manage Docker containers for running coding agents in isolation.
    
    ```!
    which geno-iso >/dev/null 2>&1 || echo "geno-iso CLI not on PATH. Run: geno-tools install geno-iso"
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `geno-iso run [NAME] [WORKSPACE]` | Create a persistent container (background, enter with `it`) |
    | `geno-iso run --rm [NAME] [WORKSPACE] -- [AGENT_ARGS]` | One-shot: run the selected agent and remove container |
    | `geno-iso ls [--all]` | List running (or all) geno-iso containers |
    | `geno-iso it [NAME] [--shell]` | Enter a running container (agent CLI or bash) |
    | `geno-iso stop [NAME]` | Stop a running container |
    | `geno-iso rm [NAME] [-f]` | Remove a container |
    | `geno-iso build [--version X.Y.Z]` | Build the Docker image |
    | `geno-iso creds [--agent claude|codex]` | Refresh host credentials used for container auth |
    
    ## Typical Workflow
    
    1. `geno-iso build` — build the image (once)
    2. `geno-iso run my-project /path/to/workspace` — create a persistent container
    3. `geno-iso it my-project` — enter it interactively (launches the agent CLI)
    4. `geno-iso it my-project --shell` — or get a bash shell
    5. `geno-iso stop my-project` / `geno-iso rm my-project` — lifecycle management
    
    ## Runtime
    
    Requires Docker. Claude credential extraction uses macOS Keychain; Codex uses the host `~/.codex` login state.
