# Nomenclature

Naming conventions for skills, skillsets, and slash commands in the geno ecosystem.

## Naming pattern

```
{skillset}-{sub-skillset}-{skill}
```

- **Skillset**: the repo name, always `geno-<domain>` (e.g., `geno-dev`, `geno-notes`)
- **Sub-skillset**: a pluralized noun grouping related skills (e.g., `loops`, `commits`, `workspaces`)
- **Skill**: an action verb (e.g., `start`, `create`, `manage`, `rewrite`)

### Examples

| Full name | Skillset | Sub-skillset | Skill |
|-----------|----------|-------------|-------|
| `geno-dev-tasks-start` | geno-dev | tasks | start |
| `geno-dev-commits-rewrite` | geno-dev | commits | rewrite |
| `geno-dev-worktrees-manage` | geno-dev | worktrees | manage |
| `geno-notes-wiki-compile` | geno-notes | wiki | compile |
| `geno-iso-containers-run` | geno-iso | containers | run |

## Slash commands

Every skill becomes a slash command with the same name:

```
/geno-dev-tasks-start
```

The `geno-` prefix is canonical in all committed files. Users can configure a shorter prefix (e.g., `gt-`) via `~/.geno/config.yaml`:

```yaml
aliases:
  command_prefix: "gt"
```

This produces `/geno-dev-tasks-start` at runtime. Never hardcode aliased prefixes in source files.

## Umbrella skills

Each skillset has an umbrella skill with the same name as the repo (e.g., `geno-dev` for the `geno-dev` skillset). The umbrella SKILL.md lists all sub-skills and provides routing guidance.
