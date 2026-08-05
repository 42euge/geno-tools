# How it works

geno-tools is the **unified control plane for agent skills** — *resolve · scope
· launch*. Raw skill registration is delegated to
[`npx skills`](npx-skills-dependencies.md); geno-tools owns everything
registration can't do: it discovers skills wherever they live, vets them before
they touch your machine, resolves dependency graphs and pinned variants, watches
how skills perform, gives you a safe loop for evolving them, and launches an
agent in an isolated container scoped to exactly the skills and MCP servers you
name in a **profile**.

## The lifecycle

Everything geno-tools does is one loop around a skillset:

```
   discover ──▶ audit ──▶ install ──▶ observe ──▶ fork ──▶ use ──▶ promote
      ▲           │                      │                            │
      │           ▼                      ▼                            │
   registry    quarantine            health cards ◀───────────────────┘
   git URLs    (failed gate)         retro queue
   absorb
```

Each stage has its own page:

| Stage | What happens | Command |
|-------|--------------|---------|
| **[Discover](discover.md)** | Find candidate skillsets in the curated registry, your org's GitHub/GitLab/Bitbucket/Gitea, the open skills ecosystem (`npx skills` format), or any git URL. | `geno-tools discover` |
| **[Audit](trust-and-audit.md)** | Untrusted sources (external URLs, ecosystem refs, absorbed packs) pass the full trust gate; trusted ones get a fast conventions check. Results cache per commit. | `geno-tools audit` (implicit in `install`) |
| **[Install](install.md)** | Clone into `~/.geno/skillsets/<name>/`, build per-skillset venvs, register skills with every agent (Claude Code, Codex, Antigravity CLI) in one shot. External skill systems are [absorbed](absorption.md) into the same format. | `geno-tools install`, `geno-tools absorb` |
| **[Observe](observe.md)** | Skill traces accumulate into per-skill health cards; unhealthy skills land in the retro queue. | `geno-trace health` |
| **[Evolve](meta-harness.md)** | Fork a variant in an isolated worktree, switch to it, compare its health against main, promote the winner. | `geno-tools fork / use / promote` |
| **[Scope & Launch](profiles-and-launch.md)** | Define a profile (skills at pinned variants + MCP servers + target agents), then launch an agent in an isolated container that sees only that bundle. | `geno-tools profile`, `resolve`, `launch` |
| **[Govern](control-surface.md)** | Keep everything current, verified, and reproducible. | `geno-tools upgrade`, `doctor`, `status` |

## A day with geno-tools

You hear about a skillset a colleague built:

```console
$ geno-tools install git@github.acme.com:platform/acme-incident-response.git
installing acme-incident-response from git@github.acme.com:platform/acme-incident-response.git
  trust: git URL (untrusted) — full audit
  audit: compliant · 1 WARN
  creating venv: ~/.geno/skillsets/acme-incident-response/venvs/main
  installing 6 skill(s) via npx skills (all agents, global)
installed acme-incident-response
```

A week later its health card looks weak, so you try an improvement without
touching the working copy:

```console
$ geno-tools fork acme-incident-response terse-prompts
$ geno-tools use acme-incident-response@terse-prompts
```

You work normally for a few days while traces accumulate against the variant,
then compare and keep the winner:

```console
$ geno-trace health acme-incident-response --compare main terse-prompts
$ geno-tools promote acme-incident-response terse-prompts
```

At no point did you edit an agent config by hand, and nothing reached your
machine without passing the gate.

## How you stay in control

Every automated behavior has a knob, and the [control surface](control-surface.md)
page maps all of them. The short version:

- **Slash commands** in your agent for conversational control (`/geno-tools-…`)
- **The CLI** for direct, scriptable control (`geno-tools …`)
- **`~/.geno/config.yaml`** for policy: discovery sources, trust gates,
  autonomy level, observability thresholds
- **Zero telemetry, local-first** — the only network calls are to git remotes
  and discovery APIs you configured
