# What geno-tools is

geno-tools is a **skillset management tool for agentic meta-ecosystems** — in
practice, a package manager for agent skills.

Coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, opencode, …) each
read skills from their own directory. geno-tools is the layer above that: it
finds skill repos, clones them, builds their runtimes, and registers them with
every agent you use — so one install lands everywhere.

It manages *skillsets*. It is not itself the skills.

## The unit: a skillset

A **skillset** is a plain git repo named `{namespace}-{slug}` — `geno-loops`,
`acme-incident-response` — containing:

| Path | Role |
|------|------|
| `SKILL.md` (root) | umbrella manifest; the agent loads this first |
| `skills/<name>/SKILL.md` | **subskillsets** — one focused capability each |
| `AGENTS.md` | agent-facing instructions |
| `pyproject.toml` (optional) | Python runtime; geno-tools builds the venv |
| `layer.json` (optional) | ecosystem category, used by discovery |

Subskillsets exist so each `SKILL.md` stays small and single-purpose. The
umbrella file gives the agent enough context to find them. All of a repo's
skills get registered in one `npx skills add` call.

The namespace prefix is the only naming rule, and it's what makes private
skillsets work: `geno-*` is public, `acme-*` is yours, same layout either way.

## What geno-tools actually does

**Resolve** — a name (`geno-loops`), a git URL, or a local path all work.
Registry entries are a *discovery cache*, not a hardcoded list: geno-tools curls
the public GitHub API for `{prefix}*` repos that expose a top-level `SKILL.md`,
tags each with its `layer.json` category, and caches the result in
`~/.geno/registry.json` (auto-refreshed when >30 min stale). Any compliant git
URL installs without ever appearing in a registry.

**Install** — clone as a bare repo, lay down a `main` worktree, build a venv if
the repo declares one, symlink its console scripts onto your PATH, then register
every skill with every known agent. Declared `requires:` are installed
recursively.

**Scope** — a *profile* (`~/.geno/profiles/*.yaml`) is a named bundle: which
skills at which variant, which MCP catalogs, which agents a session may target.
Resolving a profile lowers it to a concrete plan for one launched CLI session.

**Maintain** — `status` shows version, commit, and drift against remote main.
`upgrade` fast-forwards worktrees and rebuilds venvs only when dependencies
actually changed. `deps` prints the dependency tree. `doctor` verifies symlinks,
worktrees, and venvs. `uninstall` is the exact inverse of install, with
`--dry-run`.

## On-disk layout

All state lives under `~/.geno-tools/`, one directory per skillset:

```
~/.geno-tools/
├── .state-hash                  # bumped on any state change
└── geno-{name}/
    ├── .git/                    # bare repo
    ├── main/                    # primary worktree
    ├── .worktrees/<variant>/    # additional worktrees
    ├── venvs/<name>/            # shared by default, per-worktree if isolated
    └── active -> main           # repointed to switch variants
```

Config and caches live beside it under `~/.geno/` — `config.yaml`,
`registry.json`, `profiles/`, `traces/`, `health/`, `datasets/`.

Worktrees are the mechanism for variants: you can run two versions of the same
skillset side by side and point `active` at whichever one a session should see.

## Why it's built this way

**Discovery over curation.** A static list in the tool means every new skillset
needs a PR to this repo. Discovery means the ecosystem grows without the package
manager knowing about it.

**No privileged network.** Discovery is unauthenticated `urllib` against the
public GitHub API — no `gh`, no token, no MCP, no telemetry. Install only ever
talks to the git remote you named.

**Public tooling, private content.** An organization mirrors the convention
under its own prefix, hosts the repos on its own GitHub Enterprise / GitLab /
private mirror, and pins or vendors the CLI. Public and private skillsets share
one `~/.geno-tools/`, one venv strategy, one slash-command surface. Proprietary
prompts and data stay inside the boundary; the runtime and file format stay
upstream open source.

**Agent-agnostic.** Agent identity lives in one table (`profiles.KNOWN_AGENTS`)
mapping each agent to its skills directory. Adding an agent is one entry, not a
new code path.

## Command surface

```
geno-tools status                 # installed skillsets, versions, drift
geno-tools skills install <ref>   # name | git URL | local path
geno-tools skills upgrade [name]  # one, or all
geno-tools skills remove <name> [--keep-data]
geno-tools skills discover [--refresh]
geno-tools skills deps <name>
geno-tools skills scan [--namespace X] [--dry-run]
geno-tools skills uninstall [--dry-run] [--yes]
geno-tools update                 # update geno-tools itself
geno-tools doctor
geno-tools config show | set <dot.path> <value>
```

`gt` is the default short alias (`aliases.command_prefix` in config).

The CLI is also surfaced as skills, so an agent can drive it conversationally:
`skills/manager/*` (install, upgrade, remove, status, deps, doctor, discover),
`skills/config/*`, `skills/author/*` (scaffold a new skill or skillset), and
`skills/meta/ecosystem/*` (discover, scan, onboarding).
