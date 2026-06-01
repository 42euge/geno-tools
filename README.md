# geno-tools

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/geno-tools/)

Agent-agnostic meta package manager for AI coding agents. Discovers, absorbs, evaluates, and governs skills across Claude Code, Codex, Gemini CLI, Cursor, and OpenCode.

**Website:** <https://42euge.github.io/geno-tools>

## What it does

`geno-tools` discovers skills from open-source registries and private ecosystems, absorbs external skill systems ([vercel-labs/skills](https://github.com/vercel-labs/skills), [obra/superpowers](https://github.com/obra/superpowers), Ralphy Loop plugins) into a unified framework, and manages their full lifecycle:

- **Discovery** — find candidate skills from a curated registry, GitHub/GitLab/Bitbucket orgs, private mirrors, or any git URL
- **Absorption** — normalize heterogeneous skill formats into `SKILL.md` + `genotools.yaml`; register with all agents via a single install script
- **Auditing** — built-in compliance scanning gates every onboarding path (prompt injection, dependency hygiene, filesystem/network boundaries)
- **Per-skillset venvs** — isolated at `~/.geno-tools/geno-{name}/venvs/` (only created when a skillset ships a `pyproject.toml`)
- **Zero telemetry** — local execution, no call-home, pure shell

geno-tools itself is implemented as standalone bash resource scripts under each
sub-skillset's `resources/` directory. There is no Python runtime, no
unified CLI binary; capabilities are invoked by their script path.

## Install

geno-tools ships as a native plugin/extension on each supported coding CLI. Pick the snippet for the CLI you use — every path seeds `~/.geno/config.yaml` from `.geno/geno-tools/config/defaults.yaml` the first time the agent loads the plugin.

The bootstrap lives at `.geno/geno-tools/scripts/bootstrap.sh` and only handles config seeding. CLIs that expose a startup hook (Claude Code, OpenCode) run it automatically; others can invoke it once manually as shown below.

### Claude Code

```bash
# inside a Claude Code session
/plugin marketplace add 42euge/geno-tools
/plugin install geno-tools@geno-tools
```

The first command registers this repo as a marketplace (reads `.claude-plugin/marketplace.json`); the second installs the plugin defined in `.claude-plugin/plugin.json`. The plugin manifest's `hooks` field points at `.geno/geno-tools/hooks/hooks.json`, whose SessionStart hook runs `.geno/geno-tools/scripts/bootstrap.sh` automatically. Verify with `/plugin list`.

### Codex CLI

```bash
# inside a Codex CLI session
/plugin marketplace add 42euge/geno-tools
/plugins
# in your shell, once the plugin is on disk:
bash ~/.codex/plugins/cache/geno-tools/geno-tools/*/.geno/geno-tools/scripts/bootstrap.sh
```

The marketplace catalog at `.geno/plugins/codex-agents/plugins/marketplace.json` exposes the plugin; pick `geno-tools` from the `/plugins` browser and toggle it on. (Plugins are cached at `~/.codex/plugins/cache/geno-tools/geno-tools/<version>/`.) Codex doesn't expose a portable startup hook, so run `bootstrap.sh` once — it's idempotent.

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
bash ~/.gemini/extensions/geno-tools/.geno/geno-tools/scripts/bootstrap.sh
```

Gemini clones the repo into `~/.gemini/extensions/geno-tools/`, reads `gemini-extension.json`, and registers the bundled `skills/` and `.geno/geno-tools/hooks/hooks.json`. Restart the CLI to pick it up. Update later with `gemini extensions update geno-tools`. The one-time `bootstrap.sh` seeds `~/.geno/config.yaml`.

### Cursor

Install via Cursor's plugin manager (it reads `.cursor-plugin/plugin.json`), or clone the repo into your Cursor plugins directory. Then run the bootstrap once from wherever the plugin landed:

```bash
bash <cursor-plugins-dir>/geno-tools/.geno/geno-tools/scripts/bootstrap.sh
```

### OpenCode

Add to `opencode.json`:

```json
{ "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"] }
```

Then restart OpenCode — the bundled plugin in `.geno/plugins/opencode/plugins/geno-tools.js` registers the skills path and spawns `.geno/geno-tools/scripts/bootstrap.sh` on startup.

### Verify

After install, the following skills appear as slash commands:

```
/geno-tools            # list, install, remove skillsets
/geno-onboarding       # guided onboarding for new skillsets
/geno-icons            # generate pixel art project icons
```

To run the resource scripts directly:

```bash
ROOT="$CLAUDE_PLUGIN_ROOT"   # or wherever the plugin lives
"$ROOT/skills/manager/skills/install/resources/ls.sh" --available
"$ROOT/skills/manager/skills/install/resources/install.sh" geno-<name>
```

## Usage

Skillsets are referenced by their full repo name (e.g. `geno-<name>` in the public namespace, or `acme-<name>` for a private one) so the same form works whether the entry comes from the public registry, a private mirror, or a direct git URL.

```bash
ROOT="$CLAUDE_PLUGIN_ROOT"

"$ROOT/skills/manager/skills/install/resources/ls.sh" --available
"$ROOT/skills/manager/skills/install/resources/install.sh" geno-<name>
"$ROOT/skills/manager/skills/install/resources/install.sh" <git-url>
"$ROOT/skills/manager/skills/install/resources/ls.sh"
"$ROOT/skills/manager/skills/status/resources/status.sh"
"$ROOT/skills/self/skills/update/resources/update.sh" [geno-<name>]
"$ROOT/skills/manager/skills/install/resources/remove.sh" geno-<name> [--keep-data]
```

## Layout

```
~/.geno-tools/
└── geno-{name}/
    ├── repo/       # cloned source (or symlink to dev checkout)
    ├── venvs/      # per-skillset Python environments
    ├── scripts/    # symlinks into repo/runtime/
    └── configs/    # copy-once user-editable configs
```

## Skillsets and subskillsets

A **skillset** is a self-contained git repo named `{prefix}-{slug}` that geno-tools knows how to clone, sandbox, link, and register with any supported coding agent. The prefix is the org/brand namespace; the slug names the domain.

- `geno-<name>` — public skillset under the `geno` namespace (see [the registry](#existing-geno--repos) for current ones)
- `acme-<name>` — hypothetical private skillset under an `acme` namespace

Inside each skillset:

- `SKILL.md` at the root — the umbrella manifest the agent loads first
- `skills/<subskill>/SKILL.md` — **subskillsets**, each scoped to one focused capability (a single skillset typically ships several). geno-tools registers all of them in one shot via `npx skills add --skill '*'`.
- Optional `pyproject.toml`, runtime scripts, and copy-once configs

Subskillsets keep individual SKILL.md files small and tightly scoped, while the umbrella SKILL.md gives the agent enough context to discover them.

## Onboarding a skillset

There are two ways to make a skillset installable:

1. **Curated registry** — submit a PR adding a `name<TAB>url` line to the fallback table in `skills/geno-tools/lib/registry.sh`, or just push your repo to the `42euge` org and let registry discovery via `gh` find it.
2. **Direct git URL** — anyone can install any compliant repo without a registry entry: `install.sh https://github.com/you/your-skillset.git`. This is the recommended path for private, internal, or experimental skillsets.

A minimum viable skillset only needs an `AGENTS.md` (with a literal-copy `CLAUDE.md`), a `skills.sh.json` manifest, a `skills/{name}/SKILL.md`, and a `.geno/geno-tools/genotools.yaml`; everything else (venv, runtime symlinks, configs, subskillsets) is opt-in.

## Existing geno-* repos

All public repos in the `geno-*` namespace, grouped by role.

### Skillsets

Installable by full repo name via the install resource script:

| Repo | Description |
|------|-------------|
| [42euge/geno-agents](https://github.com/42euge/geno-agents) | Multi-agent coordination, registration, autonomous loops |
| [42euge/geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| [42euge/geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| [42euge/geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, discussion scraping |
| [42euge/geno-dev](https://github.com/42euge/geno-dev) | Developer/infrastructure skills — task execution, commit rewriting, Colab upload plumbing |

### Coordination and state

Services consumed by skillsets to coordinate sessions and persist state:

| Repo | Description |
|------|-------------|
| [42euge/geno-msg](https://github.com/42euge/geno-msg) | Inter-agent messaging — file-based storage, CLI, MCP server, and hooks for cross-session communication |
| [42euge/geno-notes](https://github.com/42euge/geno-notes) | Project journal with two-scope storage for tasks, journal, plans, and audit log |
| [42euge/geno-mon](https://github.com/42euge/geno-mon) | Agent observability for insight into agentic harnesses |

### Runtime and tooling

Lower-level building blocks that power skillsets and the agent itself:

| Repo | Description |
|------|-------------|
| [42euge/geno-cli](https://github.com/42euge/geno-cli) | Agentic coding assistant TUI powered by Gemma 4 via Ollama |
| [42euge/geno-iso](https://github.com/42euge/geno-iso) | Isolated Docker containers for running Claude Code |
| [42euge/geno-term](https://github.com/42euge/geno-term) | Terminal automation for Claude Code session recovery with iTerm2 tabs and panes |
| [42euge/geno-vla](https://github.com/42euge/geno-vla) | Vision-Language-Action MCP server for Claude Code with smart browser automation |
| [42euge/geno-bench](https://github.com/42euge/geno-bench) | Mine Claude Code session logs for failure patterns and turn observed failures into benchmark tasks |

### Meta

| Repo | Description |
|------|-------------|
| [42euge/geno-tools](https://github.com/42euge/geno-tools) | This repo — installer/manager for everything above. Also ships the bundled `geno-icons` skill for pixel-art project icons. |

## Enterprise: private skillsets, public tooling

geno-tools is built so an organization can run the same agentic stack as the open-source community without leaking proprietary prompts, code, or data.

The pattern is to mirror the `geno-*` convention under your own namespace: `{company-slug}-{skillset-slug}`. For example, an internal skillset for incident response at Acme would live in a repo named `acme-incident-response`, and a finance skillset would be `acme-finance`. Same layout, same `SKILL.md` + `genotools.yaml` + `GENO.md` + optional venv shape — just hosted privately.

How it works in practice:

1. **Pick your namespace**. Use your company slug as the prefix (`acme-`, `globex-`, etc.). All internal skillsets share that prefix the way public ones share `geno-`.
2. **Host privately**. Put the repos in your own GitHub Enterprise / GitLab / Bitbucket / private mirror. geno-tools resolves any git URL — there is no central registry it has to call out to.
3. **Run geno-tools internally**. Pin the upstream OSS release, fork it, or vendor it. The implementation is plain bash, has no telemetry, and the install flow only talks to the git remote you point it at.
4. **Mix public and private freely**. A developer can install `geno-<name>` (public) alongside a private `git@github.acme.com:platform/acme-<name>.git` URL on the same machine. They share `~/.geno-tools/`, the same venv strategy, and the same slash-command surface in Claude Code / Codex / Cursor / Gemini CLI / OpenCode.

The result: sensitive prompts, datasets, and domain knowledge stay inside the company boundary, while the runtime, the file format, and the multi-agent integrations are the same fast-moving open-source code everyone else uses. You inherit upstream improvements without giving up control of your skill content.

## License

MIT
