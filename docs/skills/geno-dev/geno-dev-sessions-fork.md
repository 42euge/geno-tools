---
title: geno-dev-sessions-fork
description: Fork an agent session
---

# geno-dev-sessions-fork

`/geno-dev-sessions-fork`

> Fork an agent session

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Usage

```
/geno-dev-sessions-fork [session] [--output <file>] [--max-messages <N>]
```


## Prerequisites

- `geno-mon` must be installed and available on `$PATH`


## Options

| Flag | Description |
|---|---|
| `<session>` | Session number, partial ID, or JSONL path (default: latest) |
| `-o <file>`, `--output <file>` | Write output to a file instead of stdout |
| `-m <N>`, `--max-messages <N>` | Maximum user messages to include (default: 50) |

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. **Discover sessions** — run `geno-mon list` to show recent sessions
2. **Select session** — use the user's argument or ask them to pick one
3. **Extract context** — run `geno-mon fork <session>` to extract the session context
4. **Deliver** — write the context to a file (if `--output` given) or display it

### Step 1 — Discover sessions

```bash
geno-mon list
```

If the user provided a session argument (number, partial ID, or path), skip the picker and go to step 3.

### Step 2 — Select session

If no session was specified, show the list output and ask the user which session to fork.

### Step 3 — Extract context

```bash
geno-mon fork <session>                    # display to stdout
geno-mon fork <session> -o context.md      # write to file
geno-mon fork <session> -m 20             # limit to last 20 user messages
```

The fork output is a structured markdown document with these sections:

- **Environment** — working directory, git branch, model
- **Files Modified** — files the session edited or created
- **Files Read** — files read but not modified
- **Commands Run** — unique shell commands executed (last 30, deduplicated)
- **Conversation History** — user messages with assistant responses and tool usage summaries

### Step 4 — Deliver

- If `--output <file>` was given, confirm the file was written
- Otherwise, display the context to the user
- Suggest how to use it: paste into a new agent session prefixed with "Continue the work described in this context"

## Use cases

- **Session continuation** — pick up where a session left off after it ended or was interrupted
- **Handoff** — pass session context to a different model or agent configuration
- **Knowledge transfer** — share what a session accomplished with other agents or team members
- **Debugging** — extract a full record of what happened in a session for analysis

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-dev-sessions-fork \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = session context extracted and delivered (displayed or written to file)
- `failure` = geno-mon not found, fork command failed, or no sessions available
- `abandoned` = user stopped early or declined to select a session

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
