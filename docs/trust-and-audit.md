# Trust & audit: the gate

Skills are code that your agent runs with your permissions, and prompts that
steer a model with access to your files. Installing one is an act of trust.
geno-tools makes that trust explicit and configurable: every path a skillset
can take onto your machine runs through the same gate, and you set the
policy for what the gate does.

## Two tiers of checks

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

## Where the gate runs

The gate covers every onboarding path:

| Path | Gate behavior |
|------|--------------|
| `geno-tools install <name-or-url>` | Full audit before anything is registered; FAIL → quarantine |
| `geno-tools upgrade` | Re-audits the diff: new deps, changed prompts, widened boundaries. An upgrade can't gain network access unnoticed. |
| `geno-tools absorb` | Converted output is audited like any repo ([details](absorption.md)) |
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
  per_source:
    "github:42euge": trust      # skip deep scans for sources you own;
                                # the gate itself still runs
  pin_updates: false   # true: `upgrade` moves only to commits that pass audit,
                       # recording the audited SHA — reproducible fleets
```

Escape hatches are always available and always loud: `--no-audit` on any
command records the bypass in the skillset's state, `doctor` and `status`
show a `⚠ unaudited` marker until a later audit passes, and
`geno-tools audit --all` re-runs the gate across everything installed.

## Limits

- Static scanning catches patterns, not intent. The trust tier raises the
  bar; true isolation is geno-iso's job (containerized sessions), and the
  two compose.
- `per_source: trust` is about *your* threat model. geno-tools ships with
  nothing trusted by default, including its own registry.
- Zero telemetry holds: audits run locally, reports stay on disk, and no
  result is ever uploaded.
