# geno-tools

geno-tools is skillset managment tool for agentic meta-ecosystems.

## What it does


## Skillsets and subskillsets

A **skillset** is a self-contained git repo named `{prefix}-{slug}` that geno-tools knows how to clone, sandbox, link, and register with any supported coding agent. The prefix is the org/brand namespace; the slug names the domain.

- `geno-<name>` — public skillset under the `geno` namespace
- `internal-<name>` — private skillset under an organizational namespace
- `yourname-<name>` — private skillset under a personal namespace

Inside each skillset:

- `genotools.yaml` at the root — where `requires:` and `version:` live
- `skills/<subskill>/SKILL.md` — **subskillsets**, each scoped to one focused capability (a single skillset typically ships several). geno-tools registers all of them in one `npx skills` call.
- Optional `pyproject.toml` for a Python runtime, and `AGENTS.md` for agent-facing instructions

Subskillsets keep individual SKILL.md files small and tightly scoped.

See [docs/skillsets.md](docs/skillsets.md) for the full contract.

## Onboarding a skillset

Two ways to make a skillset installable through `geno-tools install`:

1. **Direct git URL** — install any compliant repo with no registry entry anywhere: `geno-tools install https://github.com/you/your-skillset.git`. This is the path for private, internal, and experimental skillsets.
2. **Discovery** — push to a host geno-tools is configured to scan. A repo becomes a candidate when its name matches the configured prefix and it exposes skills; after that `geno-tools install <repo-name>` resolves by bare name. There is no curated list to PR into — discovery is a cache, not a registry.

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

Same layout either way — same `genotools.yaml` + `skills/` tree + optional venv shape — just hosted privately.

How it works in practice:

1. **Pick your namespace**. Use your org slug (`internal-`) or your own handle (`yourname-`) as the prefix. All skillsets under that namespace share the prefix the way public ones share `geno-`.
2. **Host privately**. Put the repos in your own GitHub Enterprise / GitLab / Bitbucket / private mirror. geno-tools resolves any git URL — there is no central registry it has to call out to.
3. **Run geno-tools internally**. Pin the upstream OSS release, fork it, or vendor it. The CLI is plain Python, has no telemetry, and the install flow only talks to the git remote you point it at.
4. **Mix public and private freely**. A developer can run `geno-tools install geno-<name>` (public) alongside `geno-tools install git@github.internal.example.com:platform/internal-<name>.git` (private) on the same machine. They share `~/.geno-tools/`, the same venv strategy, and the same slash-command surface in Claude Code / Codex / Antigravity CLI.

The result: sensitive prompts, datasets, and domain knowledge stay inside the company boundary, while the runtime, the file format, and the multi-agent integrations are the same fast-moving open-source code everyone else uses. You inherit upstream improvements without giving up control of your skill content.

## License

MIT
