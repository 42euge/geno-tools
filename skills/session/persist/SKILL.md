---
name: geno-tools-session-persist
description: >-
  Use when the user asks to move the current Codex or Claude Code conversation
  into a persistent tmux session, survive a disconnect, or continue in tmux by
  resuming the exact session ID.
allowed-tools: "Bash(bash *) Bash(tmux *) Bash(command -v *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# session/persist — hand the current agent session to tmux

Run the bundled helper, passing the requested tmux name when one was supplied:

```bash
bash <this-skill-directory>/scripts/persist-agent-session.sh [session-name]
```

Resolve `<this-skill-directory>` from this `SKILL.md`; do not assume the skill
was installed at a fixed home-directory path.

The helper:

- reads the exact current session ID from `CODEX_SESSION_ID`,
  `CODEX_THREAD_ID`, or `CLAUDE_CODE_SESSION_ID`;
- creates a detached tmux session in the current working directory;
- launches `codex resume <id>` or `claude --resume <id>` inside it; and
- prints the exact `tmux attach-session` command.

If no name is supplied, it chooses `<directory>-<agent>` and adds a numeric
suffix when needed. A supplied name must be unique; never attach to or replace
an existing tmux session silently.

After it succeeds, report the created name and attach command. Tell the user to
attach to the tmux session and close the original agent frontend. This is a
handoff using the same conversation ID, so the user must not keep prompting
both frontends concurrently. If `$TMUX` is already set, report that the current
session is already persistent and do not create a nested tmux server.

Official Codex reference: https://developers.openai.com/codex/cli/slash-commands#codex-resume
