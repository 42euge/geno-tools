# Skillsets

A **skillset** is the unit geno-tools manages: a plain git repo named
`{namespace}-{slug}` that it knows how to clone, sandbox, link, and register with
any supported coding agent.

For the normative audit checklist, see
[Skillset Compliance Specification](skillset-compliance.md).

## Anatomy

| Path | Role |
|------|------|
| `genotools.yaml` | the marker: this repo is a geno-tools skillset. Holds `requires:` and `version:` |
| `skills/<name>/SKILL.md` | **subskillsets** — one focused capability each |
| `AGENTS.md` | agent-facing instructions; required for compliance, though not for installation |
| `pyproject.toml` (optional) | Python runtime; `[project]` drives the venv and console scripts |
| `layer.json` (optional) | ecosystem category, read remotely by discovery |

### The root `SKILL.md` problem

Discovery currently probes for a **root `SKILL.md`** to decide a repo is a
skillset (`registry.py:132`, plus the GitLab/Bitbucket/Gitea providers in
`discovery.py`). But a root `SKILL.md` is also treated as a depth-1 skill by
`npx skills`, which **shadows the entire `skills/` tree** — it returns that one
and stops. Measured against this repo:

```
npx skills add <repo> --list              → 1 skill
npx skills add <repo> --list --full-depth → 16 skills
```

geno-tools passes `--full-depth` so its own installs are correct, but anything
using plain `npx skills` gets 1 of N. Claude Code's single-skill-plugin path
likewise requires there be *no* `skills/` directory, so having both disables it.

So the root `SKILL.md` is load-bearing for discovery and harmful for
registration. The intended fix is to make `genotools.yaml` the discovery marker
and drop the root `SKILL.md` — that keeps `SKILL.md` conformant to the [Agent
Skills spec](https://agentskills.io/specification) (`name` + `description` are
its only required fields) while geno-tools' own metadata lives in a file no
other tool claims. **Not yet implemented** — it needs the five probe sites
changed together, or conformant skillsets become undiscoverable.

## Subskillsets

A skillset typically ships several. Each `skills/<name>/SKILL.md` is scoped to
one capability, so an agent loads only what it needs.

They nest — `skills/config/set/SKILL.md` is as valid as `skills/setup/SKILL.md`.
geno-tools hands the whole tree to a single `npx skills add … --full-depth`
call rather than one call per skill. `--full-depth` is required: without it the
walk stops at the first `SKILL.md` it finds on each branch.

### Writing a good `SKILL.md`

Frontmatter is `name` + `description`. The rule worth internalizing is about
`description`: **state the triggering conditions, never the workflow.** A
description that summarizes the process creates a shortcut the agent takes
*instead of* reading the skill body — a real case had a description mentioning
"code review between tasks" cause one review where the skill's own flowchart
specified two.

```yaml
# ✗ summarizes workflow — the agent may follow this and skip the body
description: Use when executing plans — dispatches a subagent per task with review between
# ✓ triggering conditions only
description: Use when executing implementation plans with independent tasks
```

## Namespaces

The prefix is the only naming rule, and it's what makes private skillsets work
without a central registry. Three conventions, which compose freely on one
machine:

| Prefix | Convention | Example |
|--------|-----------|---------|
| `geno-` | public, upstream | `geno-loops` |
| `internal-` | organizational — one shared prefix per company or team | `internal-incident-response` |
| `yourname-` | personal — yours, not the org's | `yourname-notes` |

The organizational prefix is what a platform team standardizes on so everyone
installs the same set. The personal one is for in-progress work you don't want
to publish or push onto teammates yet. A developer can have all three installed
side by side, sharing one `~/.geno-tools/` and one venv strategy.

## Becoming installable

Three paths, in increasing order of commitment:

1. **Local source install** — `geno-tools install ~/src/your-skillset` seeds the
   managed stable copy from a local repository. To iterate on live files after
   installation, use `geno-tools dev activate ~/src/your-skillset`.
2. **Direct git URL** — `geno-tools install https://…/your-skillset.git`.
   Works for any compliant repo, with no registry entry anywhere. This is the
   recommended path for private, internal, and experimental skillsets.
3. **Discovery** — push to a host geno-tools is configured to scan (see
   `discovery.sources` in `~/.geno/config.yaml`). A repo becomes a candidate when
   its name matches the configured prefix and it exposes skills. After that,
   `geno-tools install <repo-name>` resolves by bare name. Discovery is a
   cache, not a curated list — there's nothing to PR into.

## Dependencies

A skillset declares `requires:` in its `genotools.yaml`. On install, geno-tools
resolves those recursively before finishing — so installing one skillset can
pull in the graph beneath it. Dependency resolution is part of installation,
not a separate operator command.

## Stable and development selections

Each skillset is cloned as a bare repo with a managed `main` worktree, a
`venvs/default` runtime, and an `active` symlink. That is the stable selection.

`geno-tools dev activate <checkout>` selects another local checkout without
changing managed main. geno-tools creates a checkout-specific editable runtime
under `venvs/dev-<hash>`, repoints the active source and console-script links,
re-registers agent skills, then records the selection in `dev-state.json`. If a
step fails, it restores the prior selection. `geno-tools dev deactivate <name>`
returns every surface to stable main.

Use `geno-tools dev status [name]` to see the selected source and detect drift.
Do not repoint `active` manually: source, runtime links, and registered skills
form one managed selection.

See [overview.md](overview.md) for the on-disk layout in full.
