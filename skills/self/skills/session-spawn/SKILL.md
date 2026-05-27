---
name: geno-self-session-spawn
description: >-
  Spawn a named Claude Code session in a new Terminal window with remote-control
  enabled and an initial briefing. Use when user says /geno-tools-sessions-spawn,
  wants to fork work to a separate session, or says "start a new session for X".
argument-hint: "<name> [--cwd <path>] [--briefing <file-or-text>]"
allowed-tools: "Bash(*) Read(*) Write(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
observability:
  success_signal: "new Terminal window opened with claude session running and remote-control connected"
  failure_signals:
    - "Terminal.app failed to open"
    - "claude CLI not found"
    - "remote-control failed to connect"
  knowledge_reads:
    - "current working directory for default cwd"
  knowledge_writes: []
---

# Spawn Session

Spawn a named Claude Code session in a new Terminal.app window with `--dangerously-skip-permissions`, remote-control enabled, and an initial briefing prompt — all in one command.

## Input

Parse `$ARGUMENTS` for:

- **Name** (required) — the session name (e.g. `geno-docs-architect`, `auth-refactor`)
- **`--cwd <path>`** — working directory for the new session (default: current workspace root)
- **`--briefing <file-or-text>`** — initial prompt to send. Can be a file path (read and sent) or inline text. If omitted, ask the user what the session should work on.

## Important: Local + Remote Control (NOT --remote)

This skill creates a **local interactive session** then enables **Remote Control** inside it via `/remote-control`. This is NOT the same as `claude --remote` which creates a cloud-only session that exits immediately.

The correct flow:
1. Launch `claude --dangerously-skip-permissions --name <name>` (local, interactive)
2. Once the REPL is up, type `/remote-control <name>` inside the session
3. Now the session is local AND accessible from phone/browser

**Never use:**
- `claude --remote` — creates a cloud session, not local
- `claude -p "prompt"` — runs one-shot and exits, not interactive
- iTerm2 AppleScript — use Terminal.app (macOS default)

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

### 4. Wait for session to start and handle trust prompt

Wait for the claude process to appear, then handle the directory trust prompt:

```bash
for i in $(seq 1 30); do
  if pgrep -f "claude.*--name <NAME>" > /dev/null; then
    break
  fi
  sleep 1
done
```

Note: `--dangerously-skip-permissions` does NOT skip the initial directory trust prompt ("Is this a project you created or one you trust?"). After the process starts, wait 5 seconds then send Enter to confirm trust:

```bash
sleep 5
osascript -e '
tell application "Terminal"
    activate
    tell application "System Events"
        keystroke return
    end tell
end tell'
```

Wait another 8-10 seconds for the REPL to fully initialize before sending `/remote-control`.

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
