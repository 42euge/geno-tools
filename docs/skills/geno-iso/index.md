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
| [geno-iso-containers-enter](#geno-iso-containers-enter) | `/geno-iso-containers-enter` | Interactively enter a running geno-iso container |
| [geno-iso-containers-list](#geno-iso-containers-list) | `/geno-iso-containers-list` | List geno-iso containers (running and stopped) |
| [geno-iso-containers-run](#geno-iso-containers-run) | `/geno-iso-containers-run` | Spin up an isolated coding agent container with a mounted workspace |
| [geno-iso-credentials-extract](#geno-iso-credentials-extract) | `/geno-iso-credentials-extract` | Refresh host credentials used for geno-iso container auth |
| [geno-iso-dev-guide](#geno-iso-dev-guide) | `/geno-iso-dev-guide` | Development guide for the geno-iso codebase |
| [geno-iso-images-build](#geno-iso-images-build) | `/geno-iso-images-build` | Build or rebuild the geno-iso Docker image |

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

## geno-iso-containers-enter

**Slash command:** `/geno-iso-containers-enter`
  **Arguments:** `"[container-name] [--shell]"`

> Interactively enter a running geno-iso container

??? example "Full skill definition (Level 4)"

    ## Important
    
    `geno-iso it` uses `os.execvp` to replace the current process with an interactive Docker exec session. This cannot be run from within a skill -- the user must run it directly in their terminal.
    
    ## Workflow
    
    1. Run `geno-iso ls --json` to show running containers
    2. Tell the user to run the command directly:
       - `geno-iso it {name}` — launches the agent CLI inside the container
       - `geno-iso it {name} --shell` — launches bash instead
    3. For non-interactive commands, use: `docker exec geno-iso-{name} claude -p "prompt" --max-turns 1`

## geno-iso-containers-list

**Slash command:** `/geno-iso-containers-list`

> List geno-iso containers (running and stopped)

??? example "Full skill definition (Level 4)"

    ## Workflow
    
    1. Run `geno-iso ls --all --json` to get all containers
    2. Format and present the results: name, status, image version, workspace mount
    3. Suggest next actions based on state (enter running ones, restart stopped ones)

## geno-iso-containers-run

**Slash command:** `/geno-iso-containers-run`
  **Arguments:** `"[name] [workspace-path] [--rm] [-- agent-args...]"`

> Spin up an isolated coding agent container with a mounted workspace

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — optional container name and workspace path.
    
    If empty, derive the name from the current working directory.

??? example "Full skill definition (Level 4)"

    ## Input
    
    `$ARGUMENTS` — optional container name and workspace path.
    
    If empty, derive the name from the current working directory.
    
    ## Workflow
    
    1. Check if the Docker image exists: `geno-iso ls` or `docker images geno-iso --quiet`
    2. If no image, build it: `geno-iso build`
    3. For a persistent container: `geno-iso run $ARGUMENTS`
    4. For a one-shot prompt: `geno-iso run --rm $ARGUMENTS -- -p "prompt" --max-turns 1`
    5. Report the container name and how to enter it

## geno-iso-credentials-extract

**Slash command:** `/geno-iso-credentials-extract`

> Refresh host credentials used for geno-iso container auth

??? example "Full skill definition (Level 4)"

    ## Workflow
    
    1. For Claude, run `geno-iso creds --agent claude`
    2. This reads the macOS Keychain entry `Claude Code-credentials` and writes `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_OAUTH_REFRESH_TOKEN`, and `CLAUDE_CODE_OAUTH_SCOPES` to `.env`
    3. For Codex, run `geno-iso creds --agent codex`
    4. This syncs host `~/.codex/auth.json` and `~/.codex/config.toml` for container seeding
    5. Re-run the appropriate command if container auth fails

## geno-iso-dev-guide

**Slash command:** `/geno-iso-dev-guide`

> Development guide for the geno-iso codebase

??? info "Overview (Level 3)"

    Reference for developing the geno-iso codebase. Covers the settings seeding
    pipeline, credential injection, and how Claude Code detects first-run state.

??? example "Full skill definition (Level 4)"

    Reference for developing the geno-iso codebase. Covers the settings seeding
    pipeline, credential injection, and how Claude Code detects first-run state.
    
    ## Container Settings Seeding Pipeline
    
    When `geno-iso run` creates a new container, `_seed_settings()` in `docker.py`
    runs these steps in order:
    
    1. **Copy `CLAUDE.md`** — raw `docker cp` from `~/.claude/CLAUDE.md`
    2. **Sanitize `settings.json`** — reads host settings, strips `hooks`,
       `enabledPlugins`, and `extraKnownMarketplaces` (host-only paths), writes
       via `docker exec`
    3. **Seed `__store.db`** — creates an empty SQLite database with the Drizzle
       schema (5 tables). Without this, Claude Code treats the session as brand new.
    4. **Seed `~/.claude.json`** — writes `hasCompletedOnboarding: true` plus
       workspace trust entry. This is the file that controls onboarding/theme
       picker and the "trust this folder" dialog.
    
    ### Key files inside the container
    
    | Path | Purpose |
    |------|---------|
    | `/home/agent/.claude/settings.json` | User settings (sanitized, no hooks) |
    | `/home/agent/.claude/CLAUDE.md` | Global agent instructions |
    | `/home/agent/.claude/__store.db` | Conversation history DB (empty or copied) |
    | `/home/agent/.claude_env` | Fresh OAuth env vars (written by `inject_env` at exec time) |
    | `/home/agent/.claude.json` | Onboarding flags + per-project trust state |
    
    ## Claude Code First-Run Detection
    
    Claude Code checks three things at startup:
    
    1. **Onboarding completed** — `hasCompletedOnboarding` in `~/.claude.json`.
       If false/missing, shows the theme picker.
    2. **Workspace trusted** — `projects["/home/agent/workspace"].hasTrustDialogAccepted`
       in `~/.claude.json`. If false/missing, shows "Is this a project you trust?"
    3. **Store DB exists** — `~/.claude/__store.db`. If missing, may trigger
       additional first-run behavior.
    
    ## Credential Injection
    
    OAuth tokens are short-lived. The container gets initial tokens via
    `--env-file` at creation, but these expire. The `it` command refreshes:
    
    1. `credentials.ensure_fresh()` — re-extracts from macOS Keychain if `.env`
       is older than 4 hours
    2. `docker.inject_env()` — writes `/home/agent/.claude_env` with quoted
       `export` statements
    3. `docker.exec_into()` — sources `.claude_env` before launching claude:
       `sh -c '[ -f .claude_env ] && . .claude_env; exec claude'`
    
    Values must be single-quoted because `CLAUDE_CODE_OAUTH_SCOPES` contains spaces.
    
    ## Testing the Container
    
    ```bash
    # Non-interactive smoke test (bypasses onboarding by design)
    docker exec geno-iso-dev sh -c \
      '. /home/agent/.claude_env && claude -p "say hi" --dangerously-skip-permissions'
    
    # Interactive test (catches onboarding/trust prompts)
    # Uses `script` to fake a PTY since docker exec -i alone isn't enough
    (sleep 8; echo "/exit") | docker exec -i geno-iso-dev sh -c \
      '[ -f /home/agent/.claude_env ] && . /home/agent/.claude_env; script -qc "claude" /dev/null'
    ```
    
    The `-p` flag skips onboarding entirely — always test interactively when
    changing the seeding pipeline.
    
    ## pipx Install Gotcha
    
    `geno-iso` (and `geno-tools`) are installed via `pipx install -e <path>`.
    If the editable path points to a stale copy (e.g., an Obsidian vault sync),
    changes in the workspace won't take effect. Verify with:
    
    ```bash
    pipx list --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['venvs']['geno-iso']['metadata']['main_package']['package_or_url'])"
    ```
    
    Re-point with `pipx install -e /path/to/workspace/geno-iso --force`.
    
    ## run --seed-history
    
    `geno-iso run --seed-history dev .` copies the host's full `__store.db`
    instead of creating an empty one. This lets `claude --continue` work inside
    the container with host conversation history.

## geno-iso-images-build

**Slash command:** `/geno-iso-images-build`
  **Arguments:** `"[--version X.Y.Z]"`

> Build or rebuild the geno-iso Docker image

??? example "Full skill definition (Level 4)"

    ## Workflow
    
    1. Run `geno-iso build` (or `geno-iso build --version X.Y.Z` for a specific agent CLI version)
    2. Report success and the image tag
    3. Default version is 2.1.119 — override with `--version`
