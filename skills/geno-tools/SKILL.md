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

Other geno-* skillsets are discovered at install time from the registry and any `discovery.sources` configured in `~/.geno/config.yaml` — there is no committed list. Run `skills/manager/skills/install/resources/ls.sh --available` to see what's currently visible.

## Skills

Skills are organized into 7 functional areas (full convention in [.geno/geno-docs/docs/skillsets/upstream-conventions.md](../../.geno/geno-docs/docs/skillsets/upstream-conventions.md)):

| Skill | Slash command | Leaf skills |
|-------|---------------|-------------|
| **lifecycle** | /geno-lifecycle | repo-create, skill-create, onboarding-public, onboarding-enterprise — skill & skillset authoring |
| **manager** | /geno-manager | install, status — package management of installed skillsets |
| **compliance** | /geno-compliance | audit — admission gate to the ecosystem |
| **self** | /geno-self | update, improve — geno-tools self-management |
| **assets** | /geno-assets | icons — generated branding assets |
| **config** | /geno-config | alias — user personalization |

## Resource scripts

| Capability | Path (relative to plugin root) |
|------------|-------------------------------|
| list installed | `skills/manager/skills/install/resources/ls.sh` |
| list available | `skills/manager/skills/install/resources/ls.sh --available` |
| install | `skills/manager/skills/install/resources/install.sh <repo\|url\|path>` |
| remove | `skills/manager/skills/install/resources/remove.sh <repo> [--keep-data]` |
| dependency tree | `skills/manager/skills/install/resources/deps.sh <repo>` |
| update | `skills/self/skills/update/resources/update.sh [repo]` |
| status / doctor | `skills/manager/skills/status/resources/status.sh` |
| discover candidates | `skills/lifecycle/skills/onboarding-enterprise/resources/discover.sh` |
| scan into queue | `skills/lifecycle/skills/onboarding-enterprise/resources/scan.sh` |
| trace emit / list / health / queue | `skills/self/skills/improve/resources/trace-*.sh` |

Shared bash helpers (paths, config, registry, discovery providers) live at
`skills/geno-tools/lib/` and are sourced via `lib/load.sh`.

## Source resolution

The install script's `<repo|url|path>` resolves in order:
1. Registered repo name (e.g. `geno-<name>`) → git URL. Bare slug (e.g. `<name>`) is also accepted.
2. Local directory path
3. Git URL (https:// or git@)
4. Discovered candidate from `~/.geno/config.yaml` discovery sources
