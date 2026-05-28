---
name: geno-self-improve
description: >-
  Run the self-improvement cycle — refresh health cards, triage the retro queue,
  retro unhealthy skills, mine recent sessions, and report what changed. Use when
  user says /geno-tools-improve or wants to run self-improvement.
argument-hint: "[--dry-run] [--skip-retro] [--skip-mine] [--skill <name>]"
allowed-tools: "Bash(*) Read(*) Skill(geno-dev-skills-retro)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
observability:
  success_signal: "improvement cycle completed with summary report"
  failure_signals:
    - "no traces exist yet (cold start)"
    - "retro analysis failed"
  knowledge_reads:
    - "~/.geno/traces/ (raw trace data)"
    - "~/.geno/health/ (per-skill health cards)"
    - "~/.geno/retro/queue.jsonl (queued failures)"
    - "~/.geno/datasets/manifest.json (last mine date)"
  knowledge_writes:
    - "~/.geno/health/ (refreshed cards)"
    - "~/.geno/retro/ (retro artifacts)"
---

# geno-tools-improve — Self-Improvement Cycle

Orchestrates the full self-improvement loop in one command. Refreshes health data, identifies struggling skills, runs retro analysis, optionally mines sessions, and produces a summary of ecosystem health and what was improved.

## Input

Parse `$ARGUMENTS` for:

- **`--dry-run`** — analyze and report but don't apply any patches
- **`--skip-retro`** — skip retro analysis (health report only)
- **`--skip-mine`** — skip session mining
- **`--skill <name>`** — focus on a single skill instead of the full ecosystem

## Workflow

### 1. Refresh health cards

Rebuild health cards from raw traces:

```bash
TRACE="$CLAUDE_PLUGIN_ROOT/skills/self/skills/improve/resources/trace-health.sh"
"$TRACE" --refresh
```

If `--skill <name>` was given:

```bash
"$TRACE" --refresh --skill <name>
```

If the script is missing or no traces exist yet, report "no trace data — emit traces from skills first" and stop.

### 2. Health report

Read all health cards and sort by success rate:

```bash
jq -s 'sort_by(.stats.success_rate)' ~/.geno/health/*.json \
  | jq -r '.[] | "  \(.skill | tostring | (. + (\" \" * 40))[0:40]) \((.stats.success_rate * 100 | floor) | tostring + \"%\")  (\(.stats.total_invocations) runs)\(if .needs_retro then \" ← NEEDS RETRO\" else \"\" end)"'
```

Present a table:

```
Skill Health Report
═══════════════════════════════════════════════════════════════

  Skill                                    Rate   Runs
  ────────────────────────────────────────────────────────────
  geno-dev-tasks-start                      45%   (11 runs) ← NEEDS RETRO
  geno-dev-feature-ship                     60%   (5 runs)  ← NEEDS RETRO
  geno-media-audiobook-create               85%   (20 runs)
  geno-notes                                92%   (37 runs)
  ...

  Skills needing retro: 2
  Retro queue depth: 4 entries
```

If `--skill <name>` was given, show only that skill's card in detail (error types, thrashing score, knowledge reads/writes).

### 3. Check retro queue

```bash
"$CLAUDE_PLUGIN_ROOT/skills/self/skills/improve/resources/trace-queue.sh" --json 2>/dev/null || echo "[]"
```

Count entries. If the queue has entries, list them grouped by skill:

```
Retro Queue (4 entries)
  geno-dev-tasks-start      2 failures
  geno-dev-feature-ship     1 failure
  geno-loops-turbocharge    1 failure
```

### 4. Triage — decide what to retro

Build a priority list combining:

1. Skills with `needs_retro: true` in their health card (success rate < 70% with 5+ runs)
2. Skills with entries in the retro queue
3. If `--skill <name>` was given, only that skill (regardless of health)

If the list is empty and `--skip-retro` is not set, report "all skills are healthy — nothing to retro" and skip to step 6.

If the list has entries, present it to the user:

```
Improvement targets (by priority):
  1. geno-dev-tasks-start — 45% success rate, 2 queued failures
  2. geno-dev-feature-ship — 60% success rate, 1 queued failure
  3. geno-loops-turbocharge — 1 queued failure (health: 80%)
```

Ask the user which to retro:

- **All targets** — run retro on each
- **Top target only** — just the worst one
- **Skip retro** — just wanted the health report
- *(user can also type a specific skill name)*

### 5. Run retro

For each selected target, invoke the retro skill:

- If the skill has queued failures, use batch mode: invoke `/geno-dev-skills-retro --batch --skill <name>`
- If the skill has no queued entries but `needs_retro`, use the most recent failed session: invoke `/geno-dev-skills-retro --skill <name>`
- If `--dry-run` was passed, append `--dry-run` to the retro invocation

After each retro completes, note the result (patches applied, patches rejected, no actionable signals).

### 6. Session mining (optional)

Skip this step if `--skip-mine` was passed.

Check if there are new traces since the last mine:

```bash
jq -r '.latest // "never"' ~/.geno/datasets/manifest.json 2>/dev/null || echo "never"
```

If new traces exist since the last mine and `geno-mine` is available:

```bash
geno-mine extract --since <last-mine-date>
```

Report how many examples were extracted. If `geno-mine` is not available, skip silently.

### 7. Summary report

Print a final summary:

```
Self-Improvement Summary
════════════════════════════════════════

  Health:
    Total skills tracked:  14
    Healthy (≥70%):        12
    Needs retro:           2

  Retro:
    Skills retro'd:        2
    Patches applied:       3
    Patches rejected:      0

  Mining:
    New examples:          12 (SFT: 8, DPO: 4)

  Next steps:
    • geno-dev-tasks-start patched — monitor next 5 runs
    • geno-dev-feature-ship patched — monitor next 5 runs
    • Run /geno-tools-improve again after accumulating more traces
```

Omit sections that were skipped (e.g., mining if `--skip-mine`).

## Error Recovery

- If `trace-health.sh` is missing: report "trace-health.sh not found at expected path — geno-tools install corrupted" and stop.
- If `~/.geno/traces/` is empty: report "no trace data yet — skills need to emit traces before self-improvement can run" and stop.
- If `geno-dev-skills-retro` is not available: report health only, skip retro steps, note "install geno-dev for retro analysis".
- If `geno-mine` is not available: skip mining silently.
- If retro fails for one skill, continue with the next — don't let one failure block others.

## What NOT to Do

- **Don't auto-apply patches.** Always go through the retro skill's confirmation flow.
- **Don't modify trace data.** Traces are immutable append-only records.
- **Don't run retro on healthy skills.** Only retro skills that have signals (queue entries or low success rate).
- **Don't block on missing optional tools.** Degrade gracefully — health report alone is useful.

## Completion

```bash
"$CLAUDE_PLUGIN_ROOT/skills/self/skills/improve/resources/trace-emit.sh" \
  --skill geno-tools-improve \
  --status <success|partial|failure> \
  --tool-calls <count> \
  --errors <count> \
  --tags "self-improvement" "cycle"
```

- `success` = full cycle completed (health + retro + mining)
- `partial` = health report generated but retro or mining skipped/failed
- `failure` = couldn't even generate health report
