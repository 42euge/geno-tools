# geno-tools

Meta-CLI for installing and managing coding agent skillsets in the `geno-*` ecosystem. Works with Claude Code, Codex, Gemini CLI, Cursor, and OpenCode.

**Website:** <https://42euge.github.io/geno-tools>

## What it does

`geno-tools` installs/uninstalls/dev-links curated skillset repos (each a `geno-{name}` repo) into any supported coding agent. Inspired by [vercel-labs/skills](https://github.com/vercel-labs/skills) and [obra/superpowers](https://github.com/obra/superpowers), specialized for this ecosystem:

- **Curated registry** — full repo names (`geno-<name>`, e.g. those listed below) resolve to git URLs
- **Multi-agent** — skills register with all agents via `npx skills add --agent '*'`
- **Per-skillset venvs** — isolated at `~/.geno-tools/geno-{name}/venvs/`
- **Dev-link** — point at a local checkout for meta-improvement

## Install

geno-tools ships as a native plugin/extension on each supported coding CLI. Pick the snippet for the CLI you use — every path bootstraps `~/.geno/` from `config/defaults.yaml` and self-installs the `geno-tools` shell command onto PATH (via `pipx`, falling back to `pip install --user`) the first time the agent loads the plugin.

The bootstrap lives at `scripts/bootstrap.sh`. CLIs that expose a startup hook for arbitrary commands (Claude Code, OpenCode) run it automatically. The others (Gemini CLI, Codex, Cursor) need a one-time `bash <plugin-root>/scripts/bootstrap.sh` invocation, shown inline below.

### Claude Code

```bash
# inside a Claude Code session
/plugin marketplace add 42euge/geno-tools
/plugin install geno-tools@geno-tools
```

The first command registers this repo as a marketplace (reads `.claude-plugin/marketplace.json`); the second installs the plugin defined in `.claude-plugin/plugin.json`. The SessionStart hook in `hooks/hooks.json` then runs `scripts/bootstrap.sh` automatically — no separate pipx step required. Verify with `/plugin list`.

### Codex CLI

```bash
# inside a Codex CLI session
/plugin marketplace add 42euge/geno-tools
/plugins
# in your shell, once the plugin is on disk:
bash ~/.codex/plugins/cache/geno-tools/geno-tools/*/scripts/bootstrap.sh
```

The marketplace catalog at `.agents/plugins/marketplace.json` exposes the plugin; pick `geno-tools` from the `/plugins` browser and toggle it on. (Plugins are cached at `~/.codex/plugins/cache/geno-tools/geno-tools/<version>/`.) Codex doesn't expose a portable startup hook for arbitrary commands, so run `bootstrap.sh` once — it's idempotent on later invocations.

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
bash ~/.gemini/extensions/geno-tools/scripts/bootstrap.sh
```

Gemini clones the repo into `~/.gemini/extensions/geno-tools/`, reads `gemini-extension.json`, and registers the bundled `skills/`, `commands/`, and `hooks/hooks.json`. Restart the CLI to pick it up. Update later with `gemini extensions update geno-tools`. Gemini extensions don't run arbitrary startup commands, so the one-time `bootstrap.sh` invocation is what puts `geno-tools` on PATH.

### Cursor

Install via Cursor's plugin manager (it reads `.cursor-plugin/plugin.json`), or clone the repo into your Cursor plugins directory. Then run the bootstrap once from wherever the plugin landed:

```bash
bash <cursor-plugins-dir>/geno-tools/scripts/bootstrap.sh
```

### OpenCode

Add to `opencode.json`:

```json
{ "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"] }
```

Then restart OpenCode — the bundled plugin in `.opencode/plugins/geno-tools.js` registers the skills path and spawns `scripts/bootstrap.sh` on startup, so the `geno-tools` CLI appears on PATH without any extra step.

### Verify

After install, the following skills appear as slash commands:

```
/geno-tools            # list, install, remove skillsets
/geno-onboarding       # guided onboarding for new skillsets
/geno-icons            # generate pixel art project icons
```

To use the CLI directly: `geno-tools ls --available`, `geno-tools install geno-<name>`.
If `geno-tools` isn't on PATH (because the bootstrap log shows pipx/pip is missing — see `~/.geno/bootstrap.log`), install pipx (`python3 -m pip install --user pipx`) and re-run `scripts/bootstrap.sh` from the plugin directory.

## Usage

Skillsets are referenced by their full repo name (e.g. `geno-<name>` in the public namespace, or `acme-<name>` for a private one) so the same form works whether the entry comes from the public registry, a private mirror, or a direct git URL.

```bash
geno-tools ls --available                       # registry
geno-tools install geno-<name>                  # install by full repo name from the registry
geno-tools install <git-url>                    # install any compliant repo by URL
geno-tools dev geno-<name> ~/src/geno-<name>    # link a local dev checkout
geno-tools ls                                   # installed
geno-tools doctor                               # verify links, venvs, targets
geno-tools update [geno-<name>]                 # update one or all
geno-tools remove geno-<name> [--keep-data]
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
- `commands/*.md` — slash commands surfaced as `/{configured-prefix}-*` in the agent
- Optional `pyproject.toml`, runtime scripts, and copy-once configs

Subskillsets keep individual SKILL.md files small and tightly scoped, while the umbrella SKILL.md gives the agent enough context to discover them.

## Onboarding a skillset

There are three ways to make a skillset installable through `geno-tools install`:

1. **Curated registry** — submit a PR adding `"<repo-name>": "<git-url>"` to `genotools/registry.py`. After that, `geno-tools install <repo-name>` works for everyone.
2. **Direct git URL** — anyone can install any compliant repo without a registry entry: `geno-tools install https://github.com/you/your-skillset.git`. This is the recommended path for private, internal, or experimental skillsets.
3. **Local dev link** — `geno-tools dev <repo-name> ~/src/<repo-name>` to iterate on a checkout without committing.

A minimum viable skillset only needs a root `SKILL.md` and a `commands/` directory; everything else (venv, runtime symlinks, configs, subskillsets) is opt-in.

## Existing geno-* repos

All public repos in the `geno-*` namespace, grouped by role.

### Skillsets

Installable by full repo name via `geno-tools install <repo>`:

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

The pattern is to mirror the `geno-*` convention under your own namespace: `{company-slug}-{skillset-slug}`. For example, an internal skillset for incident response at Acme would live in a repo named `acme-incident-response`, and a finance skillset would be `acme-finance`. Same layout, same `SKILL.md` + `commands/` + optional venv shape — just hosted privately.

How it works in practice:

1. **Pick your namespace**. Use your company slug as the prefix (`acme-`, `globex-`, etc.). All internal skillsets share that prefix the way public ones share `geno-`.
2. **Host privately**. Put the repos in your own GitHub Enterprise / GitLab / Bitbucket / private mirror. geno-tools resolves any git URL — there is no central registry it has to call out to.
3. **Run geno-tools internally**. Pin the upstream OSS release, fork it, or vendor it. The CLI is plain Python, has no telemetry, and the install flow only talks to the git remote you point it at.
4. **Mix public and private freely**. A developer can run `geno-tools install geno-<name>` (public) alongside `geno-tools install git@github.acme.com:platform/acme-<name>.git` (private) on the same machine. They share `~/.geno-tools/`, the same venv strategy, and the same slash-command surface in Claude Code / Codex / Cursor / Gemini CLI / OpenCode.

The result: sensitive prompts, datasets, and domain knowledge stay inside the company boundary, while the runtime, the file format, and the multi-agent integrations are the same fast-moving open-source code everyone else uses. You inherit upstream improvements without giving up control of your skill content.

## License

MIT
