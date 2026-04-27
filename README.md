# geno-tools

Meta-CLI for installing and managing coding agent skillsets in the `geno-*` ecosystem. Works with Claude Code, Codex, Gemini CLI, Cursor, and OpenCode.

## What it does

`geno-tools` installs/uninstalls/dev-links curated skillset repos (each a `geno-{name}` repo) into any supported coding agent. Inspired by [vercel-labs/skills](https://github.com/vercel-labs/skills) and [obra/superpowers](https://github.com/obra/superpowers), specialized for this ecosystem:

- **Curated registry** — short names (`media`, `research`, `kaggle`, …) resolve to git URLs
- **Multi-agent** — skills register with all agents via `npx skills add --agent '*'`
- **Per-skillset venvs** — isolated at `~/.geno-tools/geno-{name}/venvs/`
- **Dev-link** — point at a local checkout for meta-improvement

## Install

### Python CLI (required for all platforms)

```bash
pipx install git+https://github.com/42euge/geno-tools
```

### Claude Code

```bash
claude /plugin install 42euge/geno-tools
```

### Codex CLI

Clone and symlink skills into `~/.agents/skills/geno-tools`, then install the Python CLI above.

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
```

### Cursor

Install via plugin manager or clone to your Cursor plugins directory.

### OpenCode

Add to `opencode.json`:
```json
{ "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"] }
```

## Usage

```bash
geno-tools ls --available                # registry
geno-tools install media                 # install geno-media
geno-tools dev media ~/src/geno-media    # link a local dev checkout
geno-tools ls                            # installed
geno-tools doctor                        # verify links, venvs, targets
geno-tools update media
geno-tools remove media [--keep-data]
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

- `geno-media` — public skillset under the `geno` namespace covering media (TTS, video, podcasts)
- `geno-research` — public skillset for wiki-style research notes and paper generation
- `acme-finance` — hypothetical private skillset under an `acme` namespace

Inside each skillset:

- `SKILL.md` at the root — the umbrella manifest the agent loads first
- `skills/<subskill>/SKILL.md` — **subskillsets**, each scoped to one focused capability (e.g. `geno-media` ships subskillsets for `audiobook-create`, `video-manim`, `podcast-cohost`). geno-tools registers all of them in one shot via `npx skills add --skill '*'`.
- `commands/*.md` — slash commands surfaced as `/{configured-prefix}-*` in the agent
- Optional `pyproject.toml`, runtime scripts, and copy-once configs

Subskillsets keep individual SKILL.md files small and tightly scoped, while the umbrella SKILL.md gives the agent enough context to discover them.

## Onboarding a skillset

There are three ways to make a skillset installable through `geno-tools install`:

1. **Curated registry** — submit a PR adding `{slug}: <git-url>` to `genotools/registry.py`. After that, `geno-tools install <slug>` works for everyone by short name.
2. **Direct git URL** — anyone can install any compliant repo without a registry entry: `geno-tools install https://github.com/you/your-skillset.git`. This is the recommended path for private, internal, or experimental skillsets.
3. **Local dev link** — `geno-tools dev <slug> ~/src/<repo>` to iterate on a checkout without committing.

A minimum viable skillset only needs a root `SKILL.md` and a `commands/` directory; everything else (venv, runtime symlinks, configs, subskillsets) is opt-in.

## Existing geno-* repos

Skillsets currently published under the public `geno-*` namespace:

| Slug | Repo | Description |
|------|------|-------------|
| `agents` | [42euge/geno-agents](https://github.com/42euge/geno-agents) | Multi-agent coordination, registration, autonomous loops |
| `media` | [42euge/geno-media](https://github.com/42euge/geno-media) | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| `research` | [42euge/geno-research](https://github.com/42euge/geno-research) | Wiki-based research, paper generation, repo documentation |
| `kaggle` | [42euge/geno-kaggle](https://github.com/42euge/geno-kaggle) | Kaggle benchmarking, notebook upload, discussion scraping |
| `dev` | [42euge/geno-dev](https://github.com/42euge/geno-dev) | Developer utilities (planned) |

Supporting repos in the same ecosystem (not skillsets — they're services, agents, or integrations consumed by skillsets):

| Repo | Description |
|------|-------------|
| [geno-msg](https://github.com/42euge/geno-msg) | Inter-agent messaging |
| [geno-notes](https://github.com/42euge/geno-notes) | Project journal, task management, timestamped notes |
| [geno-mon](https://github.com/42euge/geno-mon) | Agent monitoring |
| [geno-bot](https://github.com/42euge/geno-bot) | Bluesky companion bot |
| [geno-colab](https://github.com/42euge/geno-colab) | Google Colab integration |
| [geno-bench](https://github.com/42euge/geno-bench) | Benchmarking infrastructure |
| [geno-term](https://github.com/42euge/geno-term) | Terminal utilities |
| [geno-vla](https://github.com/42euge/geno-vla) | Vision-language-action experiments |

## Enterprise: private skillsets, public tooling

geno-tools is built so an organization can run the same agentic stack as the open-source community without leaking proprietary prompts, code, or data.

The pattern is to mirror the `geno-*` convention under your own namespace: `{company-slug}-{skillset-slug}`. For example, an internal skillset for incident response at Acme would live in a repo named `acme-incident-response`, and a finance skillset would be `acme-finance`. Same layout, same `SKILL.md` + `commands/` + optional venv shape — just hosted privately.

How it works in practice:

1. **Pick your namespace**. Use your company slug as the prefix (`acme-`, `globex-`, etc.). All internal skillsets share that prefix the way public ones share `geno-`.
2. **Host privately**. Put the repos in your own GitHub Enterprise / GitLab / Bitbucket / private mirror. geno-tools resolves any git URL — there is no central registry it has to call out to.
3. **Run geno-tools internally**. Pin the upstream OSS release, fork it, or vendor it. The CLI is plain Python, has no telemetry, and the install flow only talks to the git remote you point it at.
4. **Mix public and private freely**. A developer can run `geno-tools install media` (public) alongside `geno-tools install git@github.acme.com:platform/acme-finance.git` (private) on the same machine. They share `~/.geno-tools/`, the same venv strategy, and the same slash-command surface in Claude Code / Codex / Cursor / Gemini CLI / OpenCode.

The result: sensitive prompts, datasets, and domain knowledge stay inside the company boundary, while the runtime, the file format, and the multi-agent integrations are the same fast-moving open-source code everyone else uses. You inherit upstream improvements without giving up control of your skill content.

## Legacy (transitional)

Some slash commands still live in this repo's `commands/` — `gt-start-task`, `gt-rewrite-commit`, `gt-config-colab`, `gt-upload-colab`, `gt-upload-kaggle`. These will migrate into `geno-dev` and `geno-kaggle` as those repos come online. Lab notes have moved to the [`geno-notes`](https://github.com/42euge/geno-notes) repo (use `/gt-notes`).

A legacy `install.sh` is still present to wire up the remaining commands and colab config. It will be removed once everything is extracted.

## License

MIT
