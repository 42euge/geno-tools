# The control surface

geno-tools is controlled at three levels, from most conversational to most
precise. All three converge on the same state under `~/.geno/`, so you can
mix them freely.

## 1. Slash commands: conversational control

Inside any supported agent, every capability is a skill. You describe intent;
the agent picks the skill and runs the CLI for you:

> "install the kaggle skillset" → `/geno-tools-manager-install` → `geno-tools install geno-kaggle`

The important property: **skills never bypass the CLI**. The agent is a
convenience layer over the same commands you could type, so nothing is
possible conversationally that isn't possible (and auditable) from the shell.

The prefix you type is yours to choose: `command_prefix` in
`~/.geno/config.yaml` renders `/geno-tools-manager-install` as
`/gt-manager-install`, `/geno-…`, or bare `/install` at install time.

## 2. The CLI: direct control

```text
lifecycle
  geno-tools install-agent [<agent>]     register with coding agents; bare = interactive picker
  geno-tools discover [--refresh]        list installable skillsets, grouped
  geno-tools install <name|url|path>     audit-gate, clone, venv, register
  geno-tools remove <name> [--keep-data]
  geno-tools upgrade [<name>]            update skillsets (re-audits changes)
  geno-tools update                      update geno-tools itself
  geno-tools status                      versions, commits, drift vs remote
  geno-tools deps <name>                 dependency tree

evolution (meta-harness)
  geno-tools fork <name> <variant> [--isolated-venv]
  geno-tools use  <name>@<variant> [--here]
  geno-tools promote <name> <variant> [--keep]
  geno-tools dev  <name> <path>          link a local checkout as a variant

trust
  geno-tools audit [<path|name>] [--json]
  geno-tools quarantine ls|release       skillsets that failed the gate

absorption
  geno-tools absorb <url> [--dry-run] [--prefix ext]

health
  geno-tools doctor [--fix]              verify the whole installation
  geno-trace health [<skill>] [--compare <a> <b>]
```

### doctor

`doctor` is the "is everything actually OK?" button. It re-derives what
should be true from the manifests and checks the disk against it:

```console
$ geno-tools doctor
geno-tools doctor
── skillsets · 6 ───────────────────────────────
  geno-media    ✓ worktree · ✓ venv · ✓ 7 skills registered
  geno-kaggle   ✓ worktree · ✗ venv missing python 3.12
  geno-notes    ✓ worktree · ✓ venv · ! 1 skill not registered in codex
── ~/.geno ─────────────────────────────────────
  config.yaml   ✓ parses · 2 discovery sources
  traces        ✓ 1,204 traces · health cards fresh
────────────────────────────────────────────────
  1 FAIL · 1 WARN  — geno-tools doctor --fix repairs both
```

Every check is read-only unless you pass `--fix`, and `--fix` prints each
repair before making it.

## 3. `~/.geno/config.yaml`: policy control

Everything automatic is governed by config rather than hardcoded defaults.
The file, annotated:

```yaml
aliases:
  command_prefix: "gt"        # what you type: /gt-…, /geno-…, or /…

discovery:
  sources:                    # where discover looks; each entry is a provider
    - kind: github
      org: 42euge
    - kind: gitlab
      group: platform/skillsets
      base_url: https://gitlab.acme.com
      prefix: acme-
      auth_env: ACME_GITLAB_TOKEN   # env var name — tokens never live here

policy:                       # the trust gate (see Trust & Audit)
  gate: block                 # block | warn | off — what a FAIL does at install
  per_source:
    "github:42euge": trust    # trusted sources skip the deep scan, not the gate
  pin_updates: false          # true = upgrades stop at audited commits only

mode: user                    # user | dev — dev enables auto-PRs from retros
autonomy: 1                   # 0 passive · 1 hook-initiated · 2 background daemon

observability:
  health_threshold: 0.7       # success rate below this flags needs_retro
  health_min_traces: 5

mining:
  enabled: true
  scrub_paths: true
  scrub_secrets: true
```

### The autonomy dial

The single most important knob. It sets how much geno-tools does *without
being asked*, and each level strictly contains the previous one:

| Level | Name | What runs on its own |
|-------|------|----------------------|
| `0` | passive | Nothing. Traces are only written when a skill completes; all maintenance is manual. |
| `1` | hook-initiated *(default)* | SessionStart/Stop hooks refresh health cards and the retro queue. Work happens only at session boundaries, in your terminal. |
| `2` | background daemon | A geno-iso housekeeping loop runs wiki compilation, session mining, retros, and discovery refresh in an isolated container. |

Per-session overrides beat the file: `GENO_AUTONOMY=0 claude` gives you a
fully passive session regardless of config; `GENO_MODE=dev` likewise.

## Precedence

When surfaces disagree, the order is:

1. **Command-line flags** (`--no-audit`, `--isolated-venv`)
2. **Environment** (`GENO_MODE`, `GENO_AUTONOMY`)
3. **`~/.geno/config.yaml`**
4. **Built-in defaults** (`geno_tools/config/defaults.yaml`)
