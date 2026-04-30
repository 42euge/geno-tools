# Getting Started

## Prerequisites

- Git
- Node.js (for `npx skills`)
- Python 3.11+

## Install geno-tools

geno-tools is installed as a native plugin in your coding agent. Pick the manifest that matches the CLI you use. On Claude Code and OpenCode the plugin's startup hook auto-installs the `geno-tools` shell command onto PATH (via `pipx`, falling back to `pip install --user`); on Gemini CLI / Codex / Cursor you run the same bootstrap script once by hand.

### Claude Code

Inside a Claude Code session:

```
/plugin marketplace add 42euge/geno-tools
/plugin install geno-tools@geno-tools
```

The first command registers this repo as a marketplace (reads `.claude-plugin/marketplace.json`); the second installs the plugin defined in `.claude-plugin/plugin.json`. The SessionStart hook then runs `scripts/bootstrap.sh`, which materializes `~/.geno/config.yaml` and pipx-installs the `geno-tools` CLI if it isn't already on PATH. Verify with `/plugin list`.

This gives you `/geno-tools install`, `/geno-tools remove`, `/geno-tools ls`, and `/geno-tools update` slash commands inside your coding agent. The command prefix is [user-configurable](skillsets/creating.md#command-prefix-aliasing).

### Gemini CLI

```bash
gemini extensions install https://github.com/42euge/geno-tools
bash ~/.gemini/extensions/geno-tools/scripts/bootstrap.sh
```

The bootstrap step is one-time — Gemini extensions don't expose a startup hook for arbitrary commands, so it has to run by hand.

### Codex CLI / Cursor / OpenCode

See the [README](https://github.com/42euge/geno-tools#install) for the per-agent install snippet. OpenCode runs `scripts/bootstrap.sh` automatically on plugin load; Codex and Cursor need a one-time `bash <plugin-root>/scripts/bootstrap.sh`.

Verify the install by listing the registry from inside your agent:

```
/geno-tools ls --available
```

## Install your first skillset

List what's available in the registry:

```
/geno-tools ls --available
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
/geno-tools install geno-<name>
```

This clones the repo, sets up any declared venvs, and wires the skill into your coding agent (slash commands appear immediately).

## Check what's installed

```
/geno-tools ls
```

```
  geno-<name>              active: main
```

## Develop a skillset locally

If you're hacking on a skillset, use `dev` to symlink your local checkout instead of cloning:

```
/geno-tools dev geno-<name> ~/src/geno-<name>
```

Edits to your local checkout take effect immediately — no reinstall needed.

## What's next?

- [CLI Reference](cli-reference.md) — full command documentation
- [Creating a Skillset](skillsets/creating.md) — build your own
- [Variants & Worktrees](architecture/variants.md) — experiment with `fork` and `use`
