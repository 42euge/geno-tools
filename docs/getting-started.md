# Getting Started

`geno-tools` is the meta package manager for the geno-* skill ecosystem. You
install it once; it then discovers, installs, and manages every other
skillset across all of your coding agents.

Supported agents: **Claude Code**, **Codex**, **Antigravity CLI**.

## 1. Install the CLI

```bash
brew install 42euge/geno/geno-tools
```

This installs the `geno-tools` command and nothing else. It does not touch
any coding agent. Verify:

```bash
geno-tools --version
```

All state the CLI creates from here on (config, installed skillsets, venvs,
traces) lives in one directory: `~/.geno/`. Upgrades are plain
`brew upgrade geno-tools`.

## 2. Register with your coding agents

The CLI is useful once your agents know about it. `install-agent` scans your
machine, shows which agents it found, and lets you pick where to register:

```console
$ geno-tools install-agent
AGENT             METHOD       CONFIG DIR
-----             ------       ----------
antigravity       file         ~/.antigravity
claude-code       CLI          ~/.claude ✓
codex             CLI          ~/.codex ✓

? register geno-tools with:  (space toggles · enter applies)
  ▸ [x] claude-code
    [ ] codex

Installing geno into claude-code via native plugin CLI:
  step 1/2  add marketplace
  $ claude plugin marketplace add 42euge/geno-tools
  step 2/2  install plugin
  $ claude plugin install geno-tools@geno-tools

✓ geno installed into claude-code
```

Registration installs the plugin and slash commands into the selected agent,
so `/geno-tools-…` works in your next session there.

If you already know the target, skip the picker and name it:

```bash
geno-tools install-agent claude-code     # one agent
geno-tools install-agent --all           # every agent detected
geno-tools install-agent --rm codex      # unregister from one
```

Registration is per-agent and reversible. Skillsets you install later
register into the same set of agents automatically.

## 3. Discover skillsets

```bash
geno-tools discover
```

Lists everything installable, grouped by category, with `✓ installed` markers:

```
geno-tools
── discover · 19 ────────────────────────────────
  Core Framework
    geno-audit     https://github.com/42euge/geno-audit.git
    geno-iso       https://github.com/42euge/geno-iso.git
  Developer Tools
    geno-loops     ✓ installed
    geno-dev       https://github.com/42euge/geno-dev.git
  ...
```

Discovery uses the public GitHub API (no auth). The list is cached and
auto-refreshes when older than 30 minutes; `geno-tools discover --refresh`
forces a fresh scan.

## 4. Install a skillset

```bash
geno-tools install geno-loops
```

Audits it, clones it, sets up an isolated venv, registers its skills with
every agent you enabled in step 2, and pulls in any dependencies
automatically. Its skills then appear as slash commands (e.g.
`/geno-loops-...`).

You can also install directly by git URL, which is useful for private repos
discovery won't see:

```bash
geno-tools install https://github.com/42euge/geno-loops.git
```

## 5. Check what you have

```bash
geno-tools status
```

Shows each installed skillset's version, commit, and whether it's behind its
remote:

```
geno-tools
── installed · 2 ───────────────────────────────
  geno-loops  0.2.0  main@94eba89  ● in-sync
  geno-notes  0.1.0  main@5f3fb1f  ▼ behind e84fa17
```

Upgrade what's behind with `geno-tools upgrade` (one skillset, or all). Remove
one with `geno-tools remove <name>`.

To update **geno-tools itself**:

```bash
brew upgrade geno-tools
```
