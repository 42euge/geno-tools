---
title: geno-tools-sessions-spawn
description: Spawn a named Claude Code session in a new Terminal window with remote-control enabled and an initial briefing
---

# geno-tools-sessions-spawn

`/geno-tools-sessions-spawn "<name> [--cwd <path>] [--briefing <file-or-text>]"`

> Spawn a named Claude Code session in a new Terminal window with remote-control enabled and an initial briefing

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

Parse `$ARGUMENTS` for:

- **Name** (required) — the session name (e.g. `geno-docs-architect`, `auth-refactor`)
- **`--cwd <path>`** — working directory for the new session (default: current workspace root)
- **`--briefing <file-or-text>`** — initial prompt to send. Can be a file path (read and sent) or inline text. If omitted, ask the user what the session should work on.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Resolve parameters

- **Name**: from first argument. Kebab-case, no spaces.
- **CWD**: from `--cwd` or detect the current workspace root (walk up for `.geno/` or use cwd)
- **Briefing**: from `--briefing` flag. If it's a file path that exists, read it. Otherwise treat as inline text. If not provided, use `AskUserQuestion` to ask what the session should do.

### 2. Write launcher script

Write a temporary launcher script that handles cwd + claude launch:

```bash
LAUNCHER="/tmp/geno-spawn-${NAME}.sh"
cat > "$LAUNCHER" << 'SCRIPT'
#!/bin/bash
cd <CWD>
exec claude --dangerously-skip-permissions --name <NAME>
SCRIPT
chmod +x "$LAUNCHER"
```

### 3. Open Terminal.app window

```bash
osascript -e 'tell application "Terminal" to do script "/tmp/geno-spawn-<NAME>.sh"'
```

### 4. Wait for session to start

Wait for the claude process to appear:

```bash
for i in $(seq 1 30); do
  if pgrep -f "claude.*--name <NAME>" > /dev/null; then
    break
  fi
  sleep 1
done
```

### 5. Enable remote-control

Once the session is running, send the `/remote-control` command via keystroke:

```bash
sleep 5
osascript -e '
tell application "Terminal"
    activate
    tell application "System Events"
        keystroke "/remote-control <NAME>"
        keystroke return
    end tell
end tell'
```

### 6. Send briefing

Wait for remote-control to connect, then send the briefing:

```bash
sleep 15
osascript -e '
tell application "Terminal"
    activate
    tell application "System Events"
        keystroke "<BRIEFING_TEXT>"
        keystroke return
    end tell
end tell'
```

If the briefing is long (>500 chars), write it to a temp file and send `Read <path> and start implementing.` instead of pasting the full text.

### 7. Report

Tell the user:
- Session name and PID
- Terminal window opened
- Remote-control URL (if visible)
- What briefing was sent

## Error Recovery

- If Terminal.app fails to open, fall back to reporting the launch command for the user to run manually
- If the claude process doesn't appear within 30 seconds, report the failure
- If keystroke injection fails (permissions), tell the user to type `/remote-control <name>` and the briefing manually
- Clean up `/tmp/geno-spawn-*.sh` launcher scripts after session starts

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-tools-sessions-spawn \
  --status <success|failure> \
  --tool-calls <count> \
  --errors <count>
```

- `success` = session running with remote-control and briefing sent
- `failure` = could not launch or connect
- `abandoned` = user cancelled before launch

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-spawn-`

- **Error recovery section** — LLMs can get stuck in retry loops or abandon tasks on first failure. Explicit fallback steps prevent both.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
