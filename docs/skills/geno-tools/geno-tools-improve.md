---
title: geno-tools-improve
description: Run the self-improvement cycle — refresh health cards, triage the retro queue, retro unhealthy skills, mine recent sessions, and report what changed
---

# geno-tools-improve

`/geno-tools-improve [--dry-run] [--skip-retro] [--skip-mine] [--skill <name>]`

> Run the self-improvement cycle — refresh health cards, triage the retro queue, retro unhealthy skills, mine recent sessions, and report what changed

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Usage

Run the full self-improvement cycle:
```
/geno-tools-improve
```

Dry-run (analyze but apply nothing):
```
/geno-tools-improve --dry-run
```

Health report only (skip retro):
```
/geno-tools-improve --skip-retro
```

Focus on a single skill:
```
/geno-tools-improve --skill geno-dev-tasks-start
```

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## What it does

1. **Refresh health cards** — rebuilds per-skill health data from raw traces (`~/.geno/traces/`)
2. **Health report** — ranks skills by success rate; flags those below 70% with 5+ runs as needing retro
3. **Retro queue** — checks `~/.geno/retro/queue.jsonl` for queued failures
4. **Triage** — combines health signals and queue entries into a prioritized improvement list
5. **Run retro** — invokes `/geno-dev-skills-retro` for each selected target (requires `geno-dev`)
6. **Session mining** — extracts new SFT/DPO examples since the last mine (requires `geno-mine`)
7. **Summary** — reports total skills tracked, healthy vs needs-retro counts, patches applied, new examples

## Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Analyze and report; don't apply any patches or write mining output |
| `--skip-retro` | Produce health report only; skip retro triage and patching |
| `--skip-mine` | Skip session mining step |
| `--skill <name>` | Focus on a single skill (use full name, e.g. `geno-dev-tasks-start`) |

## Prerequisites

- `geno-trace` must be on PATH (installed automatically with geno-tools)
- At least one trace must exist in `~/.geno/traces/`
- Retro step requires `geno-dev` to be installed (`geno-tools install geno-dev`)
- Mining step requires `geno-mine` to be installed

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-tools-improve \
  --status <success|partial|failure> \
  --tool-calls <count> \
  --errors <count> \
  --tags "self-improvement" "cycle"
```

- `success` = full cycle completed (health + retro + mining)
- `partial` = health report generated but retro or mining skipped/failed
- `failure` = couldn't generate health report

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).
- **Graceful degradation** — missing optional tools (`geno-dev`, `geno-mine`) are skipped silently; the health report alone is useful.

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
