---
title: geno-dev-skills-retro
description: Meta-harness
---

# geno-dev-skills-retro

`/geno-dev-skills-retro "[session] [--skill <name>] [--dry-run] [--batch]"`

> Meta-harness

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

Parse `$ARGUMENTS` for:

- **Session** — session ID (partial match OK), PID number, or JSONL path (optional — defaults to most recent session in this project)
- **`--skill <name>`** — skip auto-detection and target a specific skill for patching
- **`--dry-run`** — analyze and propose changes but don't write them
- **`--batch`** — process the retro queue at `~/.geno/retro/queue.jsonl` instead of a single session. Each line contains a trace ID referencing a failed skill run. Process all queued items, deduplicate findings, and present a unified patch set.

If no session is given and `--batch` is not set, list the 5 most recent sessions for this project and ask the user to pick one.


## When to Use

- A session went sideways and you want to prevent the same failure next time
- The user says "that didn't work" or "the skill keeps doing X wrong"
- After a turbocharge/cruise loop stalled or failed
- Periodic skill hygiene — retro the last N sessions to find recurring patterns

Do **not** use for one-off user errors, infrastructure failures (API outage, network), or bugs in external tools.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Locate the transcript

Resolve the session to a JSONL transcript file:

```bash
# List sessions for this project
ls -lt ~/.claude/projects/$(pwd | tr '/' '-' | sed 's/^-//')/*.jsonl | head -5
```

Also check session metadata for context:

```bash
# Match session metadata by ID prefix
python3 -c "
import json, glob
for f in glob.glob(os.path.expanduser('~/.claude/sessions/*.json')):
    with open(f) as fh:
        s = json.load(fh)
        print(f'{s.get(\"pid\")} | {s.get(\"sessionId\",\"\")[:12]} | {s.get(\"name\",\"unnamed\")} | {s.get(\"cwd\",\"\")}')
"
```

If the user gave a partial ID or PID, match it. If ambiguous, show candidates and ask.

### 1.5. Check for structured traces (preferred)

Before parsing raw transcripts, check if structured traces exist for this session:

```bash
geno-trace list --json --limit 100
```

Filter traces matching the session. If traces are found:

- Each trace gives you the skill name, outcome status, error type, tool call count, and thrashing score directly — no need to infer these from raw JSONL.
- Use `geno-trace health --skill <name>` for each involved skill to see aggregate patterns (success rate, recurring error types, whether the skill already `needs_retro`).
- For `--batch` mode: read `~/.geno/retro/queue.jsonl`, look up each trace ID via `geno-trace list`, and group findings by skill.
- Traces with `outcome.status == "failure"` or `outcome.status == "partial"` are the primary retro targets.

If traces exist and provide enough signal (skill name + error type are known), you can skip the raw transcript parsing (step 2) and jump directly to step 4 (trace to skill) with the trace metadata. Fall back to full transcript parsing only when:
- No traces exist for this session (pre-trace-era sessions)
- The trace lacks sufficient detail (`error_type` is null and you need to understand *why* it failed)

### 2. Parse the transcript

Read the JSONL file and extract a structured timeline. Use a python script (inline) to parse:

```python
import json, sys

timeline = []
with open(sys.argv[1]) as f:
    for i, line in enumerate(f):
        obj = json.loads(line.strip())
        t = obj.get('type')

        if t == 'user':
            msg = obj.get('message', {}).get('content', '')
            # Detect skill invocations
            is_skill = '<command-name>' in str(msg) or '<command-message>' in str(msg)
            timeline.append({
                'line': i, 'type': 'user', 'content': msg[:500],
                'is_skill_invocation': is_skill
            })

        elif t == 'assistant':
            blocks = obj.get('message', {}).get('content', '')
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        if block.get('type') == 'tool_use':
                            timeline.append({
                                'line': i, 'type': 'tool_call',
                                'tool': block.get('name'),
                                'input_preview': str(block.get('input', {}))[:300]
                            })
                        elif block.get('type') == 'text':
                            timeline.append({
                                'line': i, 'type': 'assistant_text',
                                'content': block['text'][:500]
                            })

        elif t == 'tool_result':
            is_err = obj.get('is_error', False)
            content = str(obj.get('content', ''))[:500]
            timeline.append({
                'line': i, 'type': 'tool_result',
                'is_error': is_err, 'content': content
            })

json.dump(timeline, sys.stdout, indent=2)
```

Write the parsed timeline to `.geno/retro/<session-id>/timeline.json`.

### 3. Identify failure signals

Scan the timeline for these signal types, in order of strength:

#### A. Hard failures (strongest signal)

- **Tool errors**: `tool_result` entries with `is_error: true`
- **Command failures**: Bash tool results containing non-zero exit codes, "command not found", "No such file", "Permission denied", stack traces
- **Repeated retries**: Same tool called 3+ times with similar input (agent stuck in a loop)

#### B. User corrections (strong signal)

- **Explicit corrections**: User messages containing negation ("no", "not that", "wrong", "stop", "don't"), redirection ("instead", "actually", "what I meant"), or frustration markers ("again", "still", "keeps")
- **Abandoned approaches**: User interrupts with a new instruction mid-workflow (the previous approach was failing)
- **Manual takeover**: User provides the exact command or code to use (agent couldn't figure it out)

#### C. Soft failures (weak signal — needs corroboration)

- **Excessive tool calls**: More than 15 tool calls between user messages (thrashing)
- **Context loss**: Agent re-reads the same file multiple times
- **Stalled progress**: Long assistant text blocks with hedging language ("I'm not sure", "let me try", "this might")

For each signal, record:
- **Where**: line number in transcript
- **What**: the failure event
- **Context**: what the agent was trying to do (preceding user message + recent tool calls)

Write findings to `.geno/retro/<session-id>/signals.md`.

### 4. Trace to skill

Determine which skill (if any) was active when the failure occurred:

1. Scan for skill invocations in user messages (`<command-name>` tags or `/skill-name` patterns)
2. Map each failure signal to the nearest preceding skill invocation
3. If `--skill` was provided, filter to only signals relevant to that skill

If no skill was invoked (plain conversation), check if the failure pattern *should* have been handled by an existing skill (e.g., agent tried to do manually what a skill automates). Flag this as a "missing skill trigger" issue.

Read the identified skill's SKILL.md:

```bash
# Check installed location first, then repo
cat ~/.agents/skills/<skill-name>/SKILL.md 2>/dev/null || \
cat ./skills/<skill-name>/SKILL.md 2>/dev/null
```

### 5. Root cause analysis

Classify each failure into one of these root cause categories:

| Category | Description | Skill fix |
|---|---|---|
| **Missing guard** | Skill doesn't check a prerequisite that failed at runtime | Add a prerequisite check or "Step 0" validation |
| **Wrong approach** | Skill prescribes method A but method B works for this case | Add conditional branch or replace approach |
| **Missing edge case** | Skill handles the happy path but not this variant | Add handling to Error Recovery or a conditional in the workflow |
| **Ambiguous instruction** | Skill's wording led the agent to misinterpret | Tighten the language, add an example or "Do NOT" entry |
| **Missing context** | Skill doesn't tell the agent to gather needed information | Add a context-gathering step early in the workflow |
| **Stale reference** | Skill references a tool, path, or API that changed | Update the reference |
| **Missing skill** | No skill covers this workflow — agent improvised and failed | Recommend creating a new skill (don't patch an unrelated one) |

Write the analysis to `.geno/retro/<session-id>/analysis.md`:

```markdown
# Retro Analysis — <session-id>

## Session
- ID: <session-id>
- Project: <project path>
- Date: <timestamp>
- Skill(s) invoked: <list>

## Failure Signals
### Signal 1: <type>
- **Line**: <n>
- **What happened**: <description>
- **Context**: <what was being attempted>

## Root Causes
### 1. <category>: <one-line summary>
- **Evidence**: <which signals point to this>
- **Skill**: <skill-name>
- **Section**: <which part of the skill is deficient>
- **Proposed fix**: <what to change>
```

### 6. Generate patch

For each root cause that maps to an existing skill, generate a targeted edit:

- Read the current SKILL.md content
- Identify the exact section to modify (use line numbers)
- Write the proposed change as an `old_string → new_string` diff
- Keep changes minimal — add what's missing, don't rewrite working sections
- Preserve the skill's existing voice and structure

Present the patch to the user in a clear format:

```markdown
## Proposed Patch: <skill-name>/SKILL.md

### Change 1: <summary>
**Root cause**: <category> — <one-line>
**Section**: <heading path, e.g., "Workflow > Step 3 > Execute">

**Before:**
> <existing text>

**After:**
> <proposed text>

**Why**: <one sentence explaining how this prevents the failure>
```

If `--dry-run`, stop here. Otherwise, proceed to step 7.

### 7. Apply (with confirmation)

Use `AskUserQuestion` to confirm each change:

- **Apply all** — write all proposed changes
- **Apply selectively** — show each change and let the user accept/reject
- **Save analysis only** — keep the retro artifacts but don't modify skills
- **Discard** — this wasn't a skill issue

For accepted changes, use the `Edit` tool to modify the skill's SKILL.md. Edit the **repo copy** (under `./skills/<name>/SKILL.md`) — the installed copy at `~/.agents/skills/` is a symlink or will be synced by `geno-tools update`.

#### Mode-aware delivery

After applying patches, create a local branch for the changes:

```bash
cd <skill-repo-root>
git checkout -b retro/<skill-name>-$(date +%Y%m%d)
git add skills/<skill-name>/SKILL.md
git commit -m "retro: patch <skill-name> — <root-cause-category>"
```

**Dev mode** (check `$GENO_MODE` env var or if cwd is in a geno-* workspace):
- Push the branch and create a PR with `gh pr create`
- Scrub the PR body: strip absolute paths (`/Users/...` → `./...`), raw code snippets from user projects, and error messages that might contain secrets
- PR body should describe *what* was patched and *why* (root cause category), not reproduce raw session content

**User mode** (default):
- Keep the branch local — do not push
- Write a notification to `~/.geno/iso/inbox.jsonl`:
  ```bash
  echo '{"type":"retro","skill":"<name>","branch":"retro/<name>-<date>","summary":"<one-line>","timestamp":"<ISO>"}' >> ~/.geno/iso/inbox.jsonl
  ```

After applying:

```bash
geno-notes note "Skills retro: patched <skill-name> — <summary of changes>" \
  --project --kind milestone 2>/dev/null || true
```

### 8. Log the retro

Write a summary to `.geno/retro/<session-id>/retro.md`:

```markdown
# Retro Summary — <date>

## Session: <session-id>
## Skills patched: <list>
## Changes applied: <count>

### Patches
1. **<skill>**: <one-line summary of change>
   - Root cause: <category>
   - Prevents: <what failure this addresses>

## Patterns noticed
<any recurring themes across this and previous retros — worth watching>
```

If this project has a geno-notes scope, also log the retro:

```bash
geno-notes note "Retro complete for session <id>: <n> patches applied to <skills>" \
  --project --kind milestone 2>/dev/null || true
```

## Multi-Session Retro

If the user says "retro the last N sessions" or provides multiple session IDs:

1. Run steps 1–5 for each session independently
2. Before step 6, cross-reference findings:
   - **Recurring failures** — same root cause across sessions → higher priority patch
   - **Contradictory signals** — one session says add X, another says remove X → flag for user
   - **Cascade** — session B failed because session A's skill patch was incomplete → compound fix
3. Deduplicate patches (don't propose the same edit twice)
4. Present a unified patch set with frequency annotations ("seen in 3/5 sessions")

## Feedback Memory Integration

After a retro is applied, check if the root cause reveals a **user preference** or **project convention** that should be saved to memory:

- If the failure was "agent used approach A but user always wants approach B" → this is a feedback memory, not just a skill patch. Save it so the preference applies across skills.
- If the failure was "agent didn't know about project constraint X" → this is a project memory. Save it.

Only save memories for patterns that transcend the specific skill being patched. Skill-specific fixes go in the skill file, not memory.

## Error Recovery

- If the transcript JSONL is malformed (truncated, corrupt), parse what you can and note the gap. A partial retro is better than none.
- If the identified skill doesn't exist (was deleted or renamed), check git history: `git log --oneline --all -- 'skills/*<name>*'`. If found, note the rename. If not, classify as "missing skill."
- If the user denies all patches, ask what they think the actual issue was. Their answer is valuable feedback — consider saving it as a feedback memory.
- If `geno-notes` is not available, skip journaling steps — don't let journal failures block the retro.

## What NOT to Do

- **Don't patch skills for infrastructure failures.** API outages, network errors, and disk full are not skill bugs.
- **Don't rewrite skills from scratch.** Retros produce targeted patches, not rewrites. If a skill needs a rewrite, that's a separate task.
- **Don't infer failures that aren't there.** If the session succeeded, say so — not every session needs a patch.
- **Don't modify the transcript.** Transcripts are immutable records. Analysis goes in `.geno/retro/`, not the JSONL.
- **Don't apply patches without user confirmation** (unless `--auto` is explicitly passed — not in v0.1).
- **Don't patch external tools.** If the failure is in `geno-notes`, `git`, or a test runner, note it but don't try to fix their code.

## Batch Mode

When `--batch` is passed:

1. Read `~/.geno/retro/queue.jsonl`. Each line is a JSON object with at minimum `{"trace_id": "..."}`.
2. For each trace ID, look up the trace via `geno-trace list --json` and match by ID.
3. Group traces by skill name. For each skill:
   - Read the skill's health card: `geno-trace health --skill <name>`
   - Collect all failure traces (status = failure or partial)
   - Cross-reference with the raw transcript only if the trace lacks `error_type`
4. Deduplicate findings — if the same root cause appears across multiple traces, present it once with a frequency annotation ("seen in N traces").
5. Present a unified patch set per skill, prioritized by:
   - Skills with `needs_retro: true` in their health card (success rate < 70%)
   - Skills with the most failure traces
   - Skills with declining success rates (recent failures outweigh older successes)
6. After processing, truncate `~/.geno/retro/queue.jsonl` to remove processed entries.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-dev-skills-retro \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors> \
  --produced ".geno/retro/<session-id>/retro.md"
```

- `success` = patches applied and accepted
- `failure` = no actionable signals found, or analysis failed
- `abandoned` = user rejected all patches or stopped early

## Runtime

No venv or scripts — pure markdown workflow. Uses inline Python for transcript parsing. Retro artifacts live in `.geno/retro/<session-id>/`.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Error recovery section** — LLMs can get stuck in retry loops or abandon tasks on first failure. Explicit fallback steps prevent both.
- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-dev](index.md)
