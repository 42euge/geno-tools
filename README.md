# geno-tools

geno-tools is skillset managment tool for agentic meta-ecosystems.

## What it does


## Skillsets and subskillsets

A **skillset** is a self-contained git repo named `{prefix}-{slug}` that geno-tools knows how to clone, sandbox, link, and register with any supported coding agent. The prefix is the org/brand namespace; the slug names the domain.

- `geno-<name>` — public skillset under the `geno` namespace
- `internal-<name>` — private skillset under an organizational namespace
- `yourname-<name>` — private skillset under a personal namespace

Inside each skillset:

- `GENO.md` at the root — the umbrella manifest the agent loads first
- `skills/<subskill>/SKILL.md` — **subskillsets**, each scoped to one focused capability (a single skillset typically ships several). geno-tools registers all of them in one shot via `npx skills add --skill '*'`.
- Optional `pyproject.toml`, runtime scripts, and copy-once configs

Subskillsets keep individual SKILL.md files small and tightly scoped, while the umbrella SKILL.md gives the agent enough context to discover them.

## Onboarding a skillset

There are two ways to make a skillset installable through `geno-tools skills install`:

1. **Curated registry** — submit a PR adding `"<repo-name>": "<git-url>"` to `geno_tools/skills_manager/registry.py`. After that, `geno-tools skills install <repo-name>` works for everyone.
2. **Direct git URL** — anyone can install any compliant repo without a registry entry: `geno-tools skills install https://github.com/you/your-skillset.git`. This is the recommended path for private, internal, or experimental skillsets.

A minimum viable skillset only needs a root `SKILL.md`, a `genotools.yaml`, and an `AGENTS.md`; everything else (venv, runtime symlinks, configs, subskillsets) is opt-in.

## Existing geno-* repos

All public repos in the `geno-*` namespace, grouped by role.

### Skillsets



### Meta

| Repo | Description |
|------|-------------|
| [42euge/geno-tools](https://github.com/42euge/geno-tools) | This repo — control plane (resolve · scope · launch) for everything above, with the folded-in geno-iso container runtime. Also ships the bundled `geno-icons` skill for pixel-art project icons. |

## Enterprise: private skillsets, public tooling

geno-tools is built so an organization can run the same agentic stack as the open-source community without leaking proprietary prompts, code, or data.

The pattern is to mirror the `geno-*` convention under your own namespace: `{your-slug}-{skillset-slug}`. Two conventions work here, and they compose:

- **Organizational** — one shared prefix for the whole company or team. An incident-response skillset lives in `internal-incident-response`, a finance one in `internal-finance`. Everyone on the team installs the same prefix.
- **Personal** — your own prefix for skillsets that are yours, not the org's: `yourname-notes`, `yourname-scratch`. Useful for in-progress work you don't want to publish or push onto teammates yet.

Same layout either way — same `SKILL.md` + `genotools.yaml` + `AGENTS.md` + optional venv shape — just hosted privately.

How it works in practice:

1. **Pick your namespace**. Use your org slug (`internal-`) or your own handle (`yourname-`) as the prefix. All skillsets under that namespace share the prefix the way public ones share `geno-`.
2. **Host privately**. Put the repos in your own GitHub Enterprise / GitLab / Bitbucket / private mirror. geno-tools resolves any git URL — there is no central registry it has to call out to.
3. **Run geno-tools internally**. Pin the upstream OSS release, fork it, or vendor it. The CLI is plain Python, has no telemetry, and the install flow only talks to the git remote you point it at.
4. **Mix public and private freely**. A developer can run `geno-tools skills install geno-<name>` (public) alongside `geno-tools skills install git@github.internal.example.com:platform/internal-<name>.git` (private) on the same machine. They share `~/.geno-tools/`, the same venv strategy, and the same slash-command surface in Claude Code / Codex / Antigravity CLI.

The result: sensitive prompts, datasets, and domain knowledge stay inside the company boundary, while the runtime, the file format, and the multi-agent integrations are the same fast-moving open-source code everyone else uses. You inherit upstream improvements without giving up control of your skill content.

## License

MIT
