# How it works

geno-tools is the **package manager and governor for agent skills**: one tool
that discovers skills wherever they live, vets them before they touch your
machine, installs them into every coding agent you use, watches how they
perform, and gives you a safe loop for evolving them.

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

| Stage | What happens | Command |
|-------|--------------|---------|
| **Discover** | Find candidate skillsets in the public registry, your org's GitHub/GitLab/Bitbucket/Gitea, or any git URL. External skill systems are [absorbed](absorption.md) into the same format. | `geno-tools discover`, `geno-tools absorb` |
| **Audit** | Every onboarding path runs the [compliance and trust gate](trust-and-audit.md): conventions, dependency hygiene, prompt-injection scan, declared filesystem/network boundaries. FAILs block by default. | `geno-tools audit` (implicit in `install`) |
| **Install** | Clone into `~/.geno/skillsets/<name>/`, build per-skillset venvs, register skills with every agent (Claude Code, Codex, Antigravity CLI) in one shot. | `geno-tools install` |
| **Observe** | Skill traces accumulate into per-skill health cards; unhealthy skills land in the retro queue. | `geno-trace health` |
| **Evolve** | Fork a variant in an isolated worktree, switch to it, compare its health against main, promote the winner. The [meta-harness](meta-harness.md). | `geno-tools fork / use / promote` |
| **Govern** | Keep everything current, verified, and reproducible. | `geno-tools upgrade`, `doctor`, `status` |

## A day with geno-tools

You hear about a skillset a colleague built:

```console
$ geno-tools install git@github.acme.com:platform/acme-incident-response.git
installing acme-incident-response from git@github.acme.com:platform/acme-incident-response.git
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
