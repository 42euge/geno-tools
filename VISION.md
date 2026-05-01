# Vision

geno-tools is an agent-agnostic meta package manager for AI coding agents. It discovers skills from both open-source and internal ecosystems and can absorb external skill systems (e.g., Superpowers, Ralphy Loop plugins) into a unified framework. A meta-harness layer evaluates, refines, and manages variations of these skills over time, while built-in auditing scans the ecosystem for compliance, allowing capabilities to evolve safely by combining external innovation with private knowledge.

## Core loop

```
discover ──→ absorb ──→ evaluate ──→ govern ──→ evolve
    │            │           │           │          │
discovery.py  install    fork/use     geno-audit  promote
registry.py   npx skills  worktrees   audit.md    merge → main
config.yaml   normalize
```

**Discover** — find candidate skills from heterogeneous sources: the curated registry (`registry.py`), GitHub/GitLab/Bitbucket orgs via config-driven discovery (`discovery.py`), private mirrors, or direct git URLs.

**Absorb** — normalize external skill systems into the unified `SKILL.md` + `genotools.yaml` contract. `geno-tools install` is the single ingestion point regardless of whether a skill originates from Vercel Labs Skills, obra/superpowers, Ralphy Loop, or a private internal repo.

**Evaluate** — the meta-harness. `fork`/`use`/`promote` with git worktrees lets operators branch a skill, experiment in isolation, and iterate without touching the primary install. Multiple variations can coexist; the best is promoted.

**Govern** — built-in auditing (`geno-audit`) scans skills for compliance before they enter any namespace. The audit checklist covers prompt injection, dependency hygiene, filesystem boundaries, network data boundaries, and multi-agent integration. Every ingestion path — public registry PRs, enterprise namespace admissions, direct-URL installs — passes through this gate.

**Evolve** — promote successful variants back to main; discard failures. Combine external innovation with private knowledge to produce skills that improve over time. The loop repeats: a promoted skill can be forked again, re-evaluated, re-audited.

## Why this matters

Agents self-improve by acquiring new skills at runtime. The meta-harness ensures those skills are tested and refined before they become defaults. Auditing ensures they are safe. The result is an ecosystem of capabilities that evolves continuously — absorbing the best of the open-source community while keeping proprietary knowledge private and compliant.
