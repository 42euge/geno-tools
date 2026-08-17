---
name: geno-tools
description: >-
  Unified geno control plane: resolve, scope, and launch skillset bundles.
  Manages skillset lifecycle, variants, profiles, and isolated container
  launches. Use when the user asks about installing/removing/updating geno
  skillsets, pinning skill variants, defining profiles, or launching an agent
  in an isolated container.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m geno_tools *)"
metadata:
  author: 42euge
  version: "0.8.0"
---

# geno-tools — Skillset Manager

Orchestrator for the geno-* ecosystem. Its own skills are organized into
category directories (`skills/<category>/<name>/SKILL.md`) — see `SKILLS.md` for
the nesting standard.

```!
which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH — run /geno-tools-setup to install it (or 'bash \$PLUGIN_ROOT/skills/setup/setup.sh')."
```

## Skills by category

| Category | Skills |
|----------|--------|
| **manager/** | `status` · `discover` · `install` · `remove` · `upgrade` · `update` · `deps` · `doctor` |
| **audit/** | `run` — ecosystem compliance auditor |
| **meta/harness/** | `fork` · `use` · `promote` — variant evaluate/evolve loop |
| **meta/ecosystem/** | `discover` · `scan` · `onboarding` — find/absorb new skillsets |
| **author/** | `skill` · `repo` — scaffold a skill / a whole skillset repo |
| **iso/** | `containers-run` · `containers-list` · `containers-enter` · `images-build` · `credentials-extract` · `housekeep` · `dev-guide` — isolated container runtime |

Registration itself is delegated to `npx skills`; geno-tools adds dependency
resolution, variant pinning, profiles, MCP catalogs, and container launch.

## CLI

- `geno-tools status` — installed skillsets: version, commit, drift vs main
- `geno-tools discover [--refresh]` — installable skillsets, grouped by category
- `geno-tools install <repo|url|path>` — clone, venv, register with all agents
- `geno-tools remove <repo> [--keep-data]` — uninstall from all agents
- `geno-tools upgrade [repo]` — upgrade installed skillset(s): pull latest + re-register
- `geno-tools update` — update geno-tools **itself** to the latest version
- `geno-tools uninstall [--dry-run] [--purge-data]` — fully remove geno-tools (inverse of install; keeps your data)
- `geno-tools deps <repo>` — dependency tree

Variants, profiles & launch:

- `geno-tools fork <name> <variant>` — create a variant worktree off main
- `geno-tools use <name>@<variant>` — activate a variant (flip symlink + re-register)
- `geno-tools promote <name> <variant>` — ff-merge a variant into main
- `geno-tools profile list|show <name>|create <name>` — manage `~/.geno/profiles/*.yaml`
- `geno-tools resolve <name>` — emit a profile's resolved plan as JSON
- `geno-tools launch <agent> --profile <name> [workspace] [--rm]` — run a CLI in a
  geno-iso container scoped to the profile (variant skills bind-mounted, MCP injected)

(`geno-tools ls` = `status`; `ls --available` = `discover`, deprecated aliases.)

## Source resolution

`<repo>` resolves in order: (1) registered repo name → git URL (bare slug also
accepted), (2) local directory path, (3) git URL (`https://` or `git@`).
