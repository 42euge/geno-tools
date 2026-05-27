# Upstream Skill Conventions

The geno ecosystem implements the broader **Agent Skills** format pioneered by Anthropic and packaged by Vercel Labs as [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) and the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI (`npx skills`). geno-* skillsets are interoperable with that format — the same `npx skills add` command installs them — but layer additional conventions on top for the geno toolchain.

This page captures what the upstream convention looks like, what geno keeps, what geno extends, and where the two diverge.

## The shared baseline

Every skill — upstream or geno — is a directory containing at minimum a `SKILL.md` with YAML frontmatter:

```markdown
---
name: skill-name
description: One sentence describing when to use this skill — include trigger phrases.
---

# Skill Title

Body the agent reads when the skill activates.
```

The frontmatter `name` and `description` are loaded at session start; the body and any sibling files load only when the skill is activated. This is the **progressive disclosure** contract that both ecosystems honor.

### Upstream skill directory layout

From [`vercel-labs/agent-skills` AGENTS.md](https://github.com/vercel-labs/agent-skills/blob/main/AGENTS.md):

```
skills/
  {skill-name}/           # kebab-case directory
    SKILL.md              # required
    scripts/              # optional — *.sh / *.mjs helpers
    references/           # optional — supporting docs loaded on demand
    lib/                  # optional — shared code for scripts
```

### Repo-level upstream layout

```
agent-skills/
├── AGENTS.md             # spec for skill authoring (CLAUDE.md is a symlink to this)
├── README.md             # human-facing catalog
├── skills.sh.json        # registry manifest (groupings on skills.sh)
├── packages/             # repo-internal tooling
└── skills/
    └── {skill-name}/...
```

## What geno keeps

| Convention | Source | geno applies it as |
|---|---|---|
| `SKILL.md` + frontmatter | upstream | identical |
| `name`, `description` frontmatter fields | upstream | required |
| Progressive disclosure (load body on activation) | upstream | identical |
| `scripts/` for executable helpers | upstream | identical |
| `references/` for on-demand docs | upstream | identical |
| `lib/` for shared script code | upstream | identical |
| Bash `#!/bin/bash` + `set -e`; Node `#!/usr/bin/env node` + `.mjs` | upstream | identical |
| Status to stderr, JSON to stdout | upstream | identical |
| Keep `SKILL.md` under 500 lines | upstream guideline | enforced by `/geno-compliance-audit` (`skills/compliance/skills/audit/SKILL.md`) |
| `npx skills add` for installation | upstream tool | wrapped by `/geno-lifecycle-install` (`skills/lifecycle/skills/install/SKILL.md`) |

## What geno extends

geno adds structure on top of the shared baseline.

### Skillset-level files (geno-only)

| File | Purpose |
|---|---|
| `genotools.yaml` | Install manifest — venv, runtime symlinks, copy-once config. See [Creating a Skillset](creating.md). |
| `GENO.md` | Single source of truth for agent instructions. `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` are pointers. |
| `SKILL.md` (umbrella) | Skillset-level skill that lists the sub-skills. |
| `TENETS.md`, `VISION.md` | Optional design intent docs. |

### Naming convention

geno enforces a three-segment skill name: `{skillset}-{sub-skillset}-{skill}` (see [Nomenclature](nomenclature.md)). Upstream uses freeform kebab-case names (`vercel-react-best-practices`, `deploy-to-vercel`).

### Nested skill trees

The skill name's segment structure can also be expressed as a directory tree. The layout is **fractal**: every node has the same shape — a `SKILL.md` plus an optional `skills/` subdirectory whose children follow the same rule.

```
geno-{skillset}/                         # depth 0 — repo root
├── SKILL.md                             # skillset umbrella
└── skills/
    ├── {skillset}/                      # depth 1 — umbrella mirror (optional)
    │   └── SKILL.md
    ├── {sub-skillset-A}/                # depth 1 — sub-skillset
    │   ├── SKILL.md                     #   sub-skillset umbrella
    │   └── skills/
    │       ├── {sub-skillset-A}/        # depth 2 — umbrella mirror (optional)
    │       │   └── SKILL.md
    │       ├── {leaf-skill-1}/          # depth 2 — leaf
    │       │   ├── SKILL.md
    │       │   ├── scripts/             #   same optional dirs as upstream
    │       │   ├── references/
    │       │   └── lib/
    │       └── {sub-sub-skillset}/      # depth 2 — recurse further
    │           ├── SKILL.md
    │           └── skills/
    │               └── {leaf-skill}/
    │                   └── SKILL.md
    └── {sub-skillset-B}/
        ├── SKILL.md
        └── skills/...
```

Two equivalent layouts produce the same fully-qualified skill name `geno-dev-tasks-start`:

=== "Flat (upstream-style)"

    ```
    geno-dev/
    └── skills/
        ├── geno-dev/SKILL.md
        ├── geno-dev-tasks-start/SKILL.md
        └── geno-dev-commits-rewrite/SKILL.md
    ```

=== "Nested (geno tree-style)"

    ```
    geno-dev/
    └── skills/
        ├── geno-dev/SKILL.md
        ├── tasks/
        │   ├── SKILL.md
        │   └── skills/
        │       └── start/SKILL.md
        └── commits/
            ├── SKILL.md
            └── skills/
                └── rewrite/SKILL.md
    ```

#### Rules

1. **Same shape at every depth** — every level under `skills/` is itself a skill directory: a `SKILL.md` and an optional `skills/` subdirectory.
2. **Name is the path** — the fully-qualified skill name is `geno-` joined to each segment of the path under `skills/` (excluding any `skills/` interstitials). The `geno-` prefix is **never** repeated in directory names along the path; segment dirs use bare nouns (`tasks`, not `geno-dev-tasks`).
3. **Umbrella mirror is optional** — at any depth, a sibling directory whose name matches the parent's segment can hold a `SKILL.md` that acts as the umbrella for that level. Useful when the level itself wants its own activation-time description. **One exception:** the skillset-root umbrella keeps the full prefixed repo name (`skills/geno-{name}/SKILL.md`) by historical convention, often as a symlink to the root `SKILL.md`. Sub-level umbrellas use the bare noun (`skills/loops/SKILL.md`, not `skills/geno-loops/SKILL.md`).
4. **Frontmatter `name:` is the source of truth** — if the directory tree and the frontmatter disagree, the frontmatter wins. The audit (`/geno-audit`) flags mismatches.
5. **Depth has no hard limit** — but practically, three segments (the geno nomenclature) is the sweet spot. Deeper trees should be justified by genuine sub-grouping (e.g. `geno-dev/skills/loops/skills/cruise/skills/...` is fine if loops have meaningful internal substructure).
6. **Mixing is allowed inside one repo** — a skillset can keep some skills flat and others nested. Both forms produce the same registered slash commands.

#### When to use which

| Choose | When |
|---|---|
| **Flat** | Skill list is short, names are stable, or the repo is single-purpose. Easier to grep, cleaner `ls`. |
| **Nested** | A sub-skillset has its own scripts, references, or shared `lib/` that all leaf skills inside it consume; or the sub-skillset itself has a meaningful umbrella body worth activating on its own. The tree co-locates shared assets with the skills that use them. |
| **Hybrid** | Most of the repo is flat, but one cluster (e.g. `loops/`) is large enough to deserve its own subtree. |

#### Per-level `scripts/`, `references/`, `lib/`

Every node in the tree may carry its own `scripts/`, `references/`, and `lib/` siblings. Resolution is **lexical** — a leaf skill at `skills/loops/skills/cruise/SKILL.md` can reference `../../lib/foo.mjs` to reach a shared library at `skills/loops/lib/foo.mjs`. This mirrors how upstream skills bundle assets, just generalized to depth N.

### Frontmatter

geno is permissive about the frontmatter shape but expects at minimum `name` and `description`. Upstream `vercel-labs/agent-skills` frequently includes:

```yaml
---
name: vercel-react-best-practices
description: ...
license: MIT
metadata:
  author: vercel
  version: "1.0.0"
---
```

The `license`, `metadata.author`, and `metadata.version` fields are valid but optional in geno. They're a good idea for skillsets you intend to publish.

### Distribution

| Mechanism | Upstream | geno |
|---|---|---|
| `npx skills add <repo>` | yes | yes (interop) |
| `geno-tools install <name>` | — | wraps `npx skills add` plus venv/config setup |
| Bundled `.zip` siblings of skill dirs | yes (e.g. `react-best-practices.zip`) | not used — skillsets are git-installed |
| Registry manifest | `skills.sh.json` | `genotools.yaml` per skillset; `GENO.md` ecosystem table at the install root |

## What diverges

Areas where the two ecosystems make different choices, with rationale.

### Names: namespacing strategy

- **Upstream:** prefix embedded in the name itself (`vercel-react-best-practices`).
- **geno:** repo name carries the namespace (`geno-dev` repo → skills like `geno-dev-tasks-start`); platforms that support plugin namespacing (e.g. Claude Code) also expose `geno-tools:geno-icons`.

### Detail layout: `rules/` directories

`vercel-labs/agent-skills` uses a `rules/` subdirectory for atomic, individually-named guideline files:

```
react-best-practices/
├── SKILL.md
├── rules/
│   ├── async-parallel.md
│   ├── bundle-barrel-imports.md
│   └── client-event-listeners.md
└── ...
```

geno doesn't standardize on `rules/` — most geno skills keep details inline or in `references/`. Skillsets that *are* rule catalogs (lint rules, style rules, review checklists) should adopt the upstream `rules/` pattern. It's already supported by the loader; nothing in geno-tools forbids it.

### Cover docs at skill root

Upstream skills frequently include sibling `README.md`, `AGENTS.md`, and `metadata.json` next to `SKILL.md`. geno currently keeps these at the skillset root only. Adding them per-skill is fine when the skill is large enough to warrant its own ecosystem (the upstream `vercel-optimize` skill is the canonical example — it has `lib/`, `references/playbooks/`, 15 mjs scripts, and its own `CONTRIBUTING.md`).

## Migration recipes

### Upstream → geno

To bring an upstream skill into a geno skillset:

1. Drop the directory into `skills/` under your geno-* repo.
2. Rename it to follow `{skillset}-{sub-skillset}-{skill}` if you want the geno slash-command shape — or place it as a leaf in a [nested tree](#nested-skill-trees) and let the path produce the name.
3. Update the `name:` in frontmatter to match.
4. Add an entry to your skillset's `GENO.md` skills table — `/geno-skills-create` does this for new skills, but for imports you'll edit by hand.

### geno → upstream-compatible

geno skills already work with `npx skills add`. To make one cleanly publishable as a standalone upstream-style skill:

1. Add `license:` and `metadata: { author, version }` to the frontmatter.
2. Decide whether to keep the long name (`geno-dev-tasks-start`) or rename to a flat upstream-style name (`tasks-start`, `start-task`).
3. If the skill has many guidelines or rules, factor them into a `rules/` subdirectory.
4. Ship a `README.md` next to `SKILL.md` for human readers.

### Flat → nested (or back)

Both forms produce the same registered slash commands, so converting is mechanical:

- **Flat → nested:** for each cluster of skills sharing a sub-skillset segment (e.g. all `geno-loops-*-*`), create a directory at that segment, move a `SKILL.md` umbrella into it, and move the leaf skills under its own `skills/` directory. Strip the now-redundant prefix from the leaf directory names. Update each leaf's frontmatter `name:` only if it was wrong.
- **Nested → flat:** walk the tree, and for each leaf `SKILL.md` rename its containing directory to the fully-qualified name (joining path segments with `-` and prepending `geno-`). Move all leaf dirs up to a single `skills/` at the skillset root. Inline shared `lib/` or `references/` either at the skillset root or inside each leaf that needed them.

## References

- [`vercel-labs/agent-skills` repo](https://github.com/vercel-labs/agent-skills) — official Vercel skill catalog with the canonical `AGENTS.md` spec.
- [`vercel-labs/skills` repo](https://github.com/vercel-labs/skills) — the `npx skills` CLI source.
- [Agent Skills format](https://agentskills.io/) — public spec the upstream conventions point at.
- [Creating a Skillset](creating.md) — geno's authoring guide.
- [Nomenclature](nomenclature.md) — geno's naming conventions.
