---
title: geno-dev-sessions-remote
description: Start a Claude Code session with remote access in a workspace directory
---

# geno-dev-sessions-remote

`/geno-dev-sessions-remote "[workspace-path] [--name <session-name>]"`

> Start a Claude Code session with remote access in a workspace directory

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Usage

```
/geno-dev-sessions-remote <workspace-path> [--name <session-name>]
/geno-dev-sessions-remote                   # uses current directory
```

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Arguments

- `$ARGUMENTS` — path to the workspace directory. If omitted, uses the current working directory.
- `--name <name>` — optional session name for the remote control session. Defaults to the directory basename.

## Workflow

1. **Resolve path** — if `$ARGUMENTS` contains a path, resolve it. If it's a workspace name, look it up under the user's code directories (`~/code-red/*/`). If empty, use `$PWD`.

2. **Validate** — confirm the directory exists. Check if it's a git repo or contains a `CLAUDE.md`.

3. **Derive session name** — use `--name` if provided, otherwise use the directory basename.

4. **Launch** — open a new Terminal window with `clauded` (alias for `claude --dangerously-skip-permissions`):
   ```bash
   osascript -e '
   tell application "Terminal"
       activate
       do script "cd <resolved-path> && clauded --remote-control <session-name>"
   end tell'
   ```

   **To resume a previous session**, use `--continue` (not `--resume`, which opens an interactive picker that blocks in the background):
   ```bash
   clauded --continue --remote-control <session-name>
   ```

5. **Confirm** — tell the user the session is starting and to check the new Terminal window for the remote access URL.

## Important

- Use `--continue` (resumes most recent session in that directory) rather than `--resume` (interactive picker) since the Terminal may not be visible and interactive input blocks silently.
- Always use `clauded` (skip permissions) not plain `claude`.
- The process needs an interactive TTY — cannot run in the background or via `&`.

## Examples

```
/geno-dev-sessions-remote /Users/euge/code-red/comfy-geno-ws/comfyGeno
/geno-dev-sessions-remote comfyGeno --name comfy
/geno-dev-sessions-remote   # current directory
```

## Notes

- The remote control session runs in a separate Terminal window because it requires an interactive TTY.
- The session name is passed to `--remote-control` and used to identify the session in the remote control UI.
- Remote sessions can be accessed from any device via the URL printed in the Terminal.
- To stop the session, close the Terminal window or press Ctrl+C.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
