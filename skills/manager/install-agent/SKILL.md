---
name: geno-tools-manager-install-agent
description: >-
  Register the geno ecosystem skill manifest into a coding agent (claude-code,
  codex, cursor, windsurf) so the agent discovers and can invoke geno skills.
  Supports custom manifests via -m flag.
allowed-tools: "Bash(geno-tools install-agent *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-tools / install-agent

Writes a skill manifest into the target agent's config directory so it
discovers all installed geno-* skillsets automatically.

## Commands

```bash
# List supported agents and their detected config dirs
geno-tools install-agent --list

# Register geno skills into Claude Code (~/.claude/plugin.json)
geno-tools install-agent claude-code

# Register into Codex
geno-tools install-agent codex

# Preview without writing anything
geno-tools install-agent claude-code --dry-run

# Use a custom manifest (e.g. a curated subset of skills)
geno-tools install-agent claude-code -m ~/my-skill-manifest.json
```

## Supported agents

| Agent | Config dir | Manifest file |
|---|---|---|
| `claude-code` | `~/.claude/` | `plugin.json` |
| `codex` | `~/.codex/` | `plugin.json` |
| `cursor` | `~/.cursor/` | `geno-plugin.json` |
| `windsurf` | `~/.codeium/windsurf/` | `geno-plugin.json` |

## How it works

Auto-detects installed geno skillsets from `~/.geno-tools/*/active/skills/`
and writes a manifest pointing at each one. The agent reads this on startup
and gains access to all installed geno skills.

Run after `geno-tools install <skillset>` to propagate new skills to your
agent without restarting it (or restart the agent to pick up the new manifest).

## Via the `geno` CLI

```bash
geno install claude-code          # delegates to this command
geno install codex -m my.json     # custom manifest
geno install --list               # list agents
```
