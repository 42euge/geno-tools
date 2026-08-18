# Skillsets

A **skillset** is the unit geno-tools manages: a plain git repo named
`{namespace}-{slug}` that it knows how to clone, sandbox, link, and register with
any supported coding agent.

## Anatomy

| Path | Role |
|------|------|
| `SKILL.md` (root) | umbrella manifest; the agent loads this first |
| `skills/<name>/SKILL.md` | **subskillsets** — one focused capability each |
| `AGENTS.md` | agent-facing instructions |
| `genotools.yaml` | skillset metadata (`requires:`, venv shape) |
| `pyproject.toml` (optional) | Python runtime; geno-tools builds the venv |
| `layer.json` (optional) | ecosystem category, read by discovery |

A minimum viable skillset is just the root `SKILL.md`, `genotools.yaml`, and
`AGENTS.md`. Everything else — venv, runtime symlinks, copy-once configs,
subskillsets — is opt-in.

## Subskillsets

A skillset typically ships several. Each `skills/<name>/SKILL.md` is scoped to
one capability, which keeps individual files small enough that an agent loads
only what it needs; the umbrella `SKILL.md` carries just enough context for the
agent to discover them.

They nest — `skills/config/set/SKILL.md` is as valid as `skills/setup/SKILL.md` —
and geno-tools registers every leaf in a single `npx skills add --skill '*'`
call rather than one call per skill.

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

1. **Local dev link** — `geno-tools skills install ~/src/your-skillset` to
   iterate on a checkout without committing anything.
2. **Direct git URL** — `geno-tools skills install https://…/your-skillset.git`.
   Works for any compliant repo, with no registry entry anywhere. This is the
   recommended path for private, internal, and experimental skillsets.
3. **Discovery** — push to a host geno-tools is configured to scan (see
   `discovery.sources` in `~/.geno/config.yaml`). A repo becomes a candidate when
   its name matches the configured prefix and it exposes a top-level `SKILL.md`.
   After that, `geno-tools skills install <repo-name>` resolves by bare name.

## Dependencies

A skillset declares `requires:` in its `genotools.yaml`. On install, geno-tools
resolves those recursively before finishing — so installing one skillset can
pull in the graph beneath it. `geno-tools skills deps <name>` prints that tree.

## Variants

Each skillset is cloned as a bare repo with a `main` worktree and an `active`
symlink pointing at it. Additional worktrees under `.worktrees/<variant>/` let
two versions of the same skillset exist at once; repointing `active` decides
which one a session sees. Venvs are shared across worktrees by default, or
per-worktree when a variant needs isolation.

See [overview.md](overview.md) for the on-disk layout in full.
