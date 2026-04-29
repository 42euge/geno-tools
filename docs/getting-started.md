# Getting Started

## Prerequisites

- Git
- Node.js (for `npx skills`)
- Python 3.11+

## Install geno-tools

geno-tools is installed as a native plugin in your coding agent. Pick the manifest that matches the CLI you use:

### Claude Code

```bash
claude /plugin install 42euge/geno-tools
```

This gives you `/gt-install`, `/gt-remove`, `/gt-ls`, and `/gt-update` slash commands inside Claude Code.

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
```

### Codex CLI / Cursor / OpenCode

See the [README](https://github.com/42euge/geno-tools#install) for the per-agent install snippet.

Verify the install by listing the registry from inside your agent:

```
/gt-ls --available
```

## Install your first skillset

List what's available in the registry:

```
/gt-ls --available
```

```
  geno-agents              https://github.com/42euge/geno-agents.git
  geno-media               https://github.com/42euge/geno-media.git
  geno-research            https://github.com/42euge/geno-research.git
  geno-kaggle              https://github.com/42euge/geno-kaggle.git
  geno-dev                 https://github.com/42euge/geno-dev.git
```

Install one:

```
/gt-install geno-<name>
```

This clones the repo, sets up any declared venvs, and wires the skill into your coding agent (slash commands appear immediately).

## Check what's installed

```
/gt-ls
```

```
  geno-<name>              active: main
```

## Develop a skillset locally

If you're hacking on a skillset, use `dev` to symlink your local checkout instead of cloning:

```
/gt-dev geno-<name> ~/src/geno-<name>
```

Edits to your local checkout take effect immediately — no reinstall needed.

## What's next?

- [CLI Reference](cli-reference.md) — full command documentation
- [Creating a Skillset](skillsets/creating.md) — build your own
- [Variants & Worktrees](architecture/variants.md) — experiment with `fork` and `use`
