# What geno-tools is

geno-tools is a **skillset management tool for agentic meta-ecosystems** — in
practice, a package manager for agent skills.

Coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, opencode, …) each
read skills from their own directory. geno-tools is the layer above that: it
finds skill repos, clones them, builds their runtimes, and registers them with
every agent you use — so one install lands everywhere.

It manages *skillsets*. It is not itself the skills.

## The unit: a skillset

A **skillset** is a plain git repo with a `SKILL.md` at its root, named
`{namespace}-{slug}`:

- `geno-loops` — public, upstream
- `internal-incident-response` — organizational namespace
- `yourname-notes` — personal namespace

The prefix is the only naming rule. That's what lets private skillsets work with
no central registry, and it's why public and private ones coexist on one machine.

→ **[skillsets.md](skillsets.md)** for anatomy, subskillsets, namespaces,
dependencies, and variants.

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

**Maintain** — `status` shows version, commit, and drift against remote main.
`update` fast-forwards worktrees, removes retired skill registrations, and
rebuilds venvs only when dependencies actually changed. Dependency resolution
is automatic during install. `dev activate` selects a local checkout together
with an isolated editable runtime, its console commands, and agent skill
registrations; `dev deactivate` restores stable main without modifying it.
`uninstall` is the inverse of installing one skillset. The guarded
`system uninstall` command removes the entire geno-tools-managed footprint,
with a dry run and explicit confirmation, while preserving user data under
`~/.geno/`.

## On-disk layout

All state lives under `~/.geno-tools/`, one directory per skillset:

```
~/.geno-tools/
└── geno-{name}/
    ├── .git/                    # bare repo
    ├── main/                    # primary worktree
    ├── venvs/
    │   ├── default/             # stable isolated Python runtime
    │   └── dev-<hash>/          # cached editable runtime per dev checkout
    ├── dev-state.json           # present only while dev mode is active
    └── active -> main|checkout  # selected skill source
```

Config and caches live beside it under `~/.geno/` — `config.yaml`,
`registry.json`, and `discovery/`.

## Why it's built this way

**Discovery over curation.** A static list in the tool means every new skillset
needs a PR to this repo. Discovery means the ecosystem grows without the package
manager knowing about it.

**No privileged network.** Discovery is unauthenticated `urllib` against the
public GitHub API — no `gh`, no token, no MCP, no telemetry. Install only ever
talks to the git remote you named.

**Public tooling, private content.** An organization — or one person — mirrors
the convention under its own prefix, hosts the repos on its own GitHub Enterprise / GitLab /
private mirror, and pins or vendors the CLI. Public and private skillsets share
one `~/.geno-tools/`, one venv strategy, one slash-command surface. Proprietary
prompts and data stay inside the boundary; the runtime and file format stay
upstream open source.

**Agent-agnostic.** Agent identity lives in one table in
`skills_manager/agents.py`. Adding an agent is one entry, not a new code path.

## Command surface

```
geno-tools status                 # installed skillsets, versions, drift
geno-tools install <ref>   # name | git URL | local path
geno-tools update [name]  # one, or all
geno-tools uninstall <name> [--keep-data]
geno-tools dev activate <checkout>
geno-tools dev status [name]
geno-tools dev deactivate <name>
geno-tools discover [--refresh]
geno-tools scan [--namespace X] [--dry-run]
geno-tools system uninstall [--dry-run] [--yes]
geno-tools system update          # update geno-tools itself
geno-tools config show | set <dot.path> <value>
```

`gt` is the default short alias (`aliases.command_prefix` in config).

The CLI is also surfaced as skills, so an agent can drive it conversationally:
`skills/manager/*` (install, upgrade, remove, status, discover, dev),
`skills/config/*`, `skills/author/*` (scaffold a new skill or skillset), and
`skills/meta/ecosystem/*` (discover, scan, onboarding).
