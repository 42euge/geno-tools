# Observe: traces and health

Every skill run emits a trace to `~/.geno/traces/`: skill name, outcome,
duration, session, and active variant. Traces aggregate into per-skill
health cards in `~/.geno/health/`.

## Health cards

```console
$ geno-trace health
geno-trace
── health · 12 skills ──────────────────────────
  geno-media-audiobook-create   0.89   64s avg   41 traces
  geno-kaggle-bench-run         0.92  312s avg   17 traces
  geno-notes-journal-add        0.61   12s avg    9 traces  ⚠ needs_retro
```

A skill drops below `health_threshold` (default 0.7, after
`health_min_traces` runs) → it lands in the retro queue:

```console
$ geno-trace queue
  geno-notes-journal-add   0.61   flagged 2d ago
```

In `mode: dev`, retros can auto-open PRs against the skill's repo.

## When collection runs

Governed by the [autonomy dial](control-surface.md#the-autonomy-dial):

- `0` — traces written on skill completion only; refresh manually
- `1` *(default)* — health cards refresh at session start/stop
- `2` — a background loop also mines sessions and processes the retro queue

## Feeding the harness

Traces are tagged with the active variant, which is what makes
[meta-harness](meta-harness.md) evaluation work:

```console
$ geno-trace health geno-media-audiobook-create --compare main faster-tts
geno-media-audiobook-create
                     main    faster-tts
  invocations:         41            18
  success rate:       71%           89%
  avg duration:       92s           64s
```

Everything stays local: traces and health cards are files on disk, never
uploaded.
