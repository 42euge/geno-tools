# Architecture

geno-tools is structured around a few core concepts:

## Source resolution

When you run `geno-tools install <name|url|path>`, the source is resolved in order:

1. **Registered short name** — looked up in `genotools/registry.py`
2. **Local directory** — installed from disk
3. **Git URL** — cloned

For URLs and local paths, the skillset name isn't known until the manifest is read, so install stages into a temporary directory first.

## Target adapters

A **target** is an agent that geno-tools writes skill files into. The adapter registry lives in `genotools/targets/`:

```python
ADAPTERS = {"claude-code": claude_code}
```

Each adapter exposes an `install()` function that writes the appropriate files (SKILL.md, slash commands) into the agent's config directory. Supported targets: Claude Code, geno-cli, with Codex and Gemini CLI adapters planned.

For Claude Code, the adapter writes to:

- `~/.claude/skills/geno-{name}/SKILL.md`
- `~/.claude/commands/*.md`

## Install flow

```
geno-tools install media
        │
        ├── resolve source (registry → git URL)
        ├── clone into ~/.geno-tools/geno-media/repo/
        ├── read genotools.yaml manifest
        ├── create venv (if declared)
        ├── symlink runtime scripts (if declared)
        ├── copy config defaults (if missing)
        └── run target adapter (write into ~/.claude/)
```

## Uninstall

Removal replays the install in reverse. Every path created during install is recorded, and `remove` walks them backwards — files before directories, directories only removed if empty. This is deterministic by construction: no globbing, no guessing.

## Pages

- [Disk Layout](layout.md) — where everything lives on disk
- [Variants & Worktrees](variants.md) — the `fork`/`use`/`promote` workflow
