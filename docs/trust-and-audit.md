# Trust & audit: the gate

Skills are code that your agent runs with your permissions, and prompts that
steer a model with access to your files. Installing one is an act of trust.
geno-tools makes that trust explicit and configurable: every path a skillset
can take onto your machine runs through the same gate, and you set the
policy for what the gate does.

## Three tiers of checks

### Conventions tier: is it a well-formed skillset?

Manifest present and parseable, semver consistency across
`genotools.yaml`/`pyproject.toml`/`SKILL.md`, every skill leaf has a
`SKILL.md`, CLI subcommands mirrored by sub-skills. Results come in three
levels: **FAIL** (blocks install), **WARN** (recommended), **INFO**
(advisory).

### Trust tier: is it safe to run?

Three check families, same FAIL/WARN/INFO reporting:

**Prompt-injection scan.** Every `SKILL.md` and prompt file is scanned for
instruction-hijack patterns: directives addressed to the agent rather than
the task ("ignore previous instructions", exfiltration requests, hidden
HTML/unicode content, base64 blobs in prose), and `allowed-tools` grants that
are broader than what the skill body uses.

**Dependency hygiene.** Python deps must be pinned or bounded; the audit
flags install-time script hooks, dependencies whose names typosquat popular
packages, and any `requires:` skillset not resolvable from your configured
discovery sources.

**Boundary declarations.** A skillset declares its runtime surface in
`genotools.yaml`:

```yaml
boundaries:
  filesystem:
    - "~/.geno/**"          # rw
    - "${workspace}/**"     # rw, resolved per-session
  network:
    - api.kaggle.com
```

The audit statically cross-checks the declaration against the code (URLs and
paths that appear in scripts but not in `boundaries:` → FAIL), and the
declaration is materialized into each agent's permission system at install
time: in Claude Code, as `allowed-tools` constraints on the generated
skills. Undeclared = unavailable.

### Rubric tier: is it performing?

The first two tiers read code. The rubric tier judges behavior: each
skillset carries a rubric that scores it against evidence from your own
traces, so the gate also catches the skillset that is well-formed and safe
but bad at its job.

A rubric lives at `~/.geno/rubrics/<skillset>.yaml` and holds two kinds of
criteria:

```yaml
criteria:
  - id: success-rate
    kind: metric              # computed from trace data
    metric: success
    min: 0.75
  - id: latency
    kind: metric
    metric: avg_duration_s
    max: 90
  - id: thrashing
    kind: metric              # retry loops and repeated tool calls per session
    metric: retries_per_trace
    max: 2
  - id: asks-before-destructive
    kind: judged              # an agent scores sampled traces against the prompt
    prompt: "Did the skill confirm before deleting or overwriting user files?"
    source: human-review      # seeded from your retro note, 2026-07-12
```

**Metric criteria** are computed directly from trace data: success rate,
latency, retries, token cost. **Judged criteria** are natural-language
checks that an agent scores against sampled traces. Judged criteria start
from human review; verdicts you leave in retros seed the rubric, and the
agent may propose new criteria from failure patterns it notices. A proposal
stays `proposed` until you accept it, and only accepted criteria gate
anything.

The rubric tier needs evidence, so it works differently from the static
tiers:

| Path | Rubric behavior |
|------|-----------------|
| first install | No evidence yet; the tier is skipped and a baseline starts accumulating |
| `geno-tools upgrade` | The new version's traces are scored against the rubric; regression past a `min`/`max` bound warns or blocks, per policy |
| `geno-tools promote` | The variant must beat main on the rubric, not just on raw success rate ([meta-harness](meta-harness.md)) |

Because it scores your own observed traces rather than the author's code,
the rubric tier applies to every installed skillset regardless of trust
level.

## Trust levels

The gate's depth scales with where the code comes from. Auditing your own
packages on every install is noise; auditing other people's is the point.

| Trust | Applies to | What runs |
|-------|-----------|-----------|
| trusted | The curated registry and sources you configure (your org, your namespaces) | Conventions tier only |
| untrusted | Arbitrary git URLs, skills-ecosystem refs, absorbed packs | Conventions + full trust tier |

Audit results cache per commit SHA. A repo audited once is never re-audited
until its content changes, so repeat installs and unchanged upgrades skip
the gate entirely.

## Where the gate runs

| Path | Gate behavior |
|------|--------------|
| `geno-tools install <registry-name>` | Trusted: conventions check, no deep scan |
| `geno-tools install <url>` / `skills:<ref>` | Untrusted: full audit before anything is registered; FAIL → quarantine |
| `geno-tools upgrade` | Re-audits the diff only: new deps, changed prompts, widened boundaries. An upgrade can't gain network access unnoticed. |
| `geno-tools absorb` | Untrusted by definition; converted output gets the strictest scan ([details](absorption.md)) |
| `geno-tools dev` | Audits but never blocks (it's your checkout); trust findings print as warnings |

A gated failure looks like:

```console
$ geno-tools install geno-sketchy
installing geno-sketchy from https://github.com/42euge/geno-sketchy.git
audit · geno-sketchy  (~/.geno/quarantine/geno-sketchy)
  [FAIL] boundary: undeclared network host  pastebin.com in scripts/sync.py
  [WARN] GENO.md (single source of truth)
  [WARN] AGENTS.md present
────────────────────────────────────────────────
  1 FAIL · 2 WARN  — required checks must pass to be installable
  quarantined: ~/.geno/quarantine/geno-sketchy
  review:    geno-tools quarantine ls
  override:  geno-tools install geno-sketchy --no-audit
```

Nothing from a quarantined repo is registered with any agent; the clone and
its audit report are kept so you can inspect exactly what failed.

## Your policy

The gate's behavior is yours to set in `~/.geno/config.yaml`:

```yaml
policy:
  gate: block          # block: FAIL stops install (default)
                       # warn:  print and continue
                       # off:   conventions tier only
  trust:
    registry: trusted           # the curated geno registry
    "github:42euge": trusted    # sources you own
    default: untrusted          # everything else: URLs, skills refs, absorbed
  pin_updates: false   # true: `upgrade` moves only to commits that pass audit,
                       # recording the audited SHA — reproducible fleets
  rubric: warn         # warn (default) | block — what a rubric regression
                       # does on upgrade and promote
```

Escape hatches are always available and always loud: `--no-audit` on any
command records the bypass in the skillset's state, `doctor` and `status`
show a `⚠ unaudited` marker until a later audit passes, and
`geno-tools audit --all` re-runs the gate across everything installed.

## Limits

- Static scanning catches patterns, not intent. The trust tier raises the
  bar; true isolation is geno-iso's job (containerized sessions), and the
  two compose.
- The `trust:` map is *your* threat model. The defaults trust only the
  curated registry and sources you configured yourself; every outside URL
  and ecosystem ref starts untrusted. Set `registry: untrusted` to gate
  everything.
- Zero telemetry holds: audits run locally, reports stay on disk, and no
  result is ever uploaded.
