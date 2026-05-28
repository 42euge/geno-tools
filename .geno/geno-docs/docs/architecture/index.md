# Architecture

geno-tools is an agent-agnostic meta package manager structured around a five-phase skill lifecycle: **discover, absorb, evaluate, govern, evolve**. This page covers the core architectural components that implement that lifecycle.

## Skill lifecycle

```
discover ──→ absorb ──→ evaluate ──→ govern ──→ evolve
    │            │           │           │          │
discovery.py  install    fork/use     geno-audit  promote
registry.py   npx skills  worktrees   audit.md    merge → main
config.yaml   normalize
```

Discovery finds candidates from heterogeneous sources (public registries, private GitHub/GitLab/Bitbucket orgs, direct URLs). Absorption normalizes them via `geno-tools install` into the `SKILL.md` + `genotools.yaml` contract. Evaluation uses the variant worktree system (`fork`/`use`/`promote`) to experiment in isolation. Governance runs the audit checklist before skills enter any namespace. Evolution promotes successful variants back to main, and the loop repeats.

## Multi-agent installation

geno-tools is installed as a native plugin on each supported coding CLI:

- **Claude Code** — `/plugin marketplace add 42euge/geno-tools` then `/plugin install geno-tools@geno-tools`
- **Codex CLI** — clone + symlink to `~/.agents/skills/geno-tools`
- **Cursor** — install via plugin manager
- **Gemini CLI** — `gemini extensions install https://github.com/42euge/geno-tools`
- **OpenCode** — add `"geno-tools@git+https://github.com/42euge/geno-tools.git"` to `opencode.json` plugins

Each plugin manifest points at the shared `skills/` directory and the bundled Python package. On Claude Code (SessionStart hook) and OpenCode (plugin loader), the bundled `scripts/bootstrap.sh` self-installs the `geno-tools` shell command onto PATH via `pipx` (with a `pip install --user` fallback) the first time the agent loads the plugin — no separate pipx step. On Gemini CLI / Codex / Cursor, whose plugin formats don't expose a startup hook for arbitrary commands, the install instructions show a one-time `bash <plugin-root>/scripts/bootstrap.sh` invocation. The ecosystem skillsets geno-tools manages are registered with all agents via `npx skills add --agent '*'`.

## Source resolution

When you run `geno-tools install <name|url|path>`, the source is resolved in order:

1. **Registered repo name** — looked up in `genotools/registry.py`
2. **Local directory** — installed from disk
3. **Git URL** — cloned
4. **Discovery sources** — repos found in configured GitHub / GitLab / etc. groups (see `genotools/discovery.py`)

For URLs and local paths, the skillset name isn't known upfront. geno-tools does a shallow clone to a staging directory, reads `pyproject.toml` for the project name, then proceeds with the full install.

## Install flow

```
geno-tools install geno-<name>
        │
        ├── resolve source (registry → git URL)
        ├── bare clone into ~/.geno-tools/geno-<name>/.git/
        ├── create main worktree
        ├── create venv + editable install (if pyproject.toml exists)
        ├── symlink [project.scripts] binaries into ~/.local/bin/
        ├── set active -> main symlink
        └── npx skills add --agent '*' (register skills with all agents)
```

On failure at any step, the partially created `~/.geno-tools/geno-<name>/` directory is cleaned up automatically.

## Uninstall

Removal reverses the install:

1. `npx skills remove` — unregister skills from all agents
2. Remove `~/.local/bin/` symlinks that point into this skillset's venv
3. Delete `~/.geno-tools/geno-<name>/` (or preserve venvs/worktrees with `--keep-data`)

## Plugin structure

The geno-tools repo ships platform-specific plugin manifests (following `obra/superpowers` conventions) alongside the Python CLI:

```
geno-tools/
├── .claude-plugin/plugin.json   # Claude Code plugin manifest
├── .codex-plugin/plugin.json    # Codex CLI plugin manifest
├── .cursor-plugin/plugin.json   # Cursor plugin manifest
├── .opencode/                   # OpenCode plugin
│   ├── plugins/geno-tools.js    #   ES module (registers skills path)
│   └── INSTALL.md
├── gemini-extension.json        # Gemini CLI extension descriptor
├── GEMINI.md                    # Gemini CLI bootstrap context
├── package.json                 # npm metadata (OpenCode entry point)
├── skills/geno-tools/SKILL.md   # umbrella skill (platform-agnostic)
├── commands/                    # slash commands (platform-agnostic)
│   ├── gt-install.md
│   ├── gt-remove.md
│   ├── gt-ls.md
│   └── gt-update.md
├── genotools/                   # Python CLI package
│   ├── cli.py
│   ├── commands.py
│   ├── paths.py
│   └── registry.py
└── pyproject.toml               # Python package metadata
```

Skills and commands are shared across all platforms. Each CLI has its own manifest that points at these shared directories.

## Meta-harness

The `fork`/`use`/`promote` workflow documented in [Variants & Worktrees](variants.md) constitutes the meta-harness: a system that drives evaluation and iteration of skills over time. Operators branch a skill into an isolated worktree, test modifications against real workloads, and promote the winner back to main. Multiple variations can coexist — the meta-harness manages the state so the active variant is always explicit.

Combined with auditing, the meta-harness enables skills to evolve safely: experiment freely in isolation, but nothing reaches the default install path without passing the compliance gate.

## Auditing

Auditing is a core architectural pillar, not an optional add-on. Every skill that enters the ecosystem — whether from the public registry, an enterprise namespace, or a direct URL — passes through the compliance gate. The `geno-audit` skill and the [audit checklist](../onboarding/audit.md) cover prompt injection, dependency hygiene, filesystem boundaries, network data boundaries, and multi-agent integration.

New ingestion paths must integrate with the audit system before shipping. See the [Audit Process](../onboarding/audit.md) for the full specification.

## Pages

- [Disk Layout](layout.md) — where everything lives on disk
- [Variants & Worktrees](variants.md) — the `fork`/`use`/`promote` workflow
