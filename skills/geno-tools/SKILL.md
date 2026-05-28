---
name: geno-tools
description: >-
  Meta package manager for geno-* skillsets. Use when user asks about
  installing, removing, listing, or updating geno ecosystem skillsets.
allowed-tools: "Bash(*) Read(*)"
metadata:
  author: 42euge
  version: "0.2.0"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Manages installation, removal, and
updates of skillset repos. Each capability lives as a standalone shell script
under the relevant sub-skillset's `resources/` directory; there is no unified
`geno-tools` CLI binary — invoke the resource scripts directly.

## Available Skillsets

Install by full repo name. Resource scripts live under
`$PLUGIN_ROOT/skills/lifecycle/skills/install/resources/`:

```bash
$PLUGIN_ROOT/skills/lifecycle/skills/install/resources/install.sh geno-<name>
```

| Repo | Description |
|------|-------------|
| geno-agents | Agent coordination, presence, and multi-agent networking |
| geno-media | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
| geno-research | Wiki-based research notes, paper generation, repo docs |
| geno-kaggle | Kaggle benchmarks, competition notebooks, discussion scraping |
| geno-dev | Developer utilities, Colab uploads, commit rewriting |

## Sub-skillsets

Skills are organized into 6 functional areas (full convention in [.geno/geno-docs/docs/skillsets/upstream-conventions.md](../../.geno/geno-docs/docs/skillsets/upstream-conventions.md)):

| Sub-skillset | Slash command | Skills |
|--------------|---------------|--------|
| **lifecycle** | /geno-lifecycle | repo-create, skill-create, install, status — skill & skillset CRUD |
| **compliance** | /geno-compliance | audit, onboarding — admission gate to the ecosystem |
| **self** | /geno-self | update, improve, session-spawn, docs-open — geno-tools self-management |
| **workspaces** | /geno-workspaces | data-init — data workspace scaffolding |
| **assets** | /geno-assets | icons — generated branding assets |
| **config** | /geno-config | alias — user personalization |

## Resource scripts

| Capability | Path (relative to plugin root) |
|------------|-------------------------------|
| list installed | `skills/lifecycle/skills/install/resources/ls.sh` |
| list available | `skills/lifecycle/skills/install/resources/ls.sh --available` |
| install | `skills/lifecycle/skills/install/resources/install.sh <repo\|url\|path>` |
| remove | `skills/lifecycle/skills/install/resources/remove.sh <repo> [--keep-data]` |
| dependency tree | `skills/lifecycle/skills/install/resources/deps.sh <repo>` |
| update | `skills/self/skills/update/resources/update.sh [repo]` |
| status / doctor | `skills/lifecycle/skills/status/resources/status.sh` |
| discover candidates | `skills/compliance/skills/onboarding/resources/discover.sh` |
| scan into queue | `skills/compliance/skills/onboarding/resources/scan.sh` |
| build mkdocs pages | `skills/self/skills/docs-open/resources/docs-build.sh` |
| trace emit / list / health / queue | `skills/self/skills/improve/resources/trace-*.sh` |

Shared bash helpers (paths, config, registry, discovery providers) live at
`skills/geno-tools/lib/` and are sourced via `lib/load.sh`.

## Source resolution

The install script's `<repo|url|path>` resolves in order:
1. Registered repo name (e.g. `geno-<name>`) → git URL. Bare slug (e.g. `<name>`) is also accepted.
2. Local directory path
3. Git URL (https:// or git@)
4. Discovered candidate from `~/.geno/config.yaml` discovery sources
