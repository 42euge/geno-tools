# Architecture

`geno-tools` is a skills-first catalog package for coding agents. It is organized around a five-phase workflow: **discover, absorb, govern, evolve**.

## Skill lifecycle

This repo contributes the skill definitions; orchestration and installation commands are handled by the external CLI/runtime in the broader geno ecosystem.

```
discover ──→ absorb ──→ govern ──→ evolve
    │            │           │         │
catalog  skillsets    audit     review
```

Discovery and absorption are surfaced to users as catalog workflows (`/geno-tools` and related skills), while governance is enforced by existing onboarding/audit checks in this repo.

## Multi-agent installation

`geno-tools` is installed as a native plugin on each supported coding CLI:

- **Claude Code** — `/plugin marketplace add 42euge/geno-tools` then `/plugin install geno-tools@geno-tools`
- **Codex CLI** — clone + symlink to `~/.agents/skills/geno-tools`
- **Cursor** — install via plugin manager
- **Antigravity CLI** — `agy plugin install https://github.com/42euge/geno-tools`
- **OpenCode** — add `"geno-tools@git+https://github.com/42euge/geno-tools.git"` to `opencode.json` plugins

## Source resolution

Within this repo, skillset candidates are discovered through:

- the curated list in [`docs/skillsets/index.md`](../skillsets/index.md),
- local `SKILL.md`/`genotools.yaml` definitions in any compliant repo,
- or external installation tooling used by the ecosystem.

This repository itself does not perform local `install`/`update`/`remove` execution.

## Plugin structure

The repo ships shared skill definitions and documentation via platform manifests:

```
geno-tools/
├── .claude-plugin/
├── .codex-plugin/
├── .cursor-plugin/
├── plugin.json
├── .opencode/
│   ├── plugins/geno-tools.js
│   └── INSTALL.md
├── package.json
├── skills/                      # shared SKILL.md definitions
└── docs/                        # documentation and architecture views
```

This keeps behavior consistent across agents while leaving runtime orchestration to the external CLI/runtime.

## Auditing

Auditing is a core architectural pillar, not an optional add-on. Every skill that enters the ecosystem — whether from the public registry, an enterprise namespace, or a direct URL — passes through the compliance gate. The `geno-audit` skill and the [audit checklist](../onboarding/audit.md) cover prompt injection, dependency hygiene, filesystem boundaries, network data boundaries, and multi-agent integration.

New ingestion paths must integrate with the audit system before shipping. See the [Audit Process](../onboarding/audit.md) for the full specification.

## Pages

- [Disk Layout](layout.md) — where everything lives on disk
