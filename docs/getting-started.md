# Getting Started

Supported agents: **Claude Code**, **Codex**, **Antigravity CLI**.

## 1. Install the CLI

```bash
brew install 42euge/geno/geno-tools
```

CLI only; no agent is touched. All state lives in `~/.geno/`.

```bash
geno-tools --version
```

## 2. Register with your agents

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

Or skip the picker:

```bash
geno-tools install-agent claude-code     # one agent
geno-tools install-agent --all           # every agent detected
geno-tools install-agent --rm codex      # unregister from one
```

## 3. Discover skillsets

```bash
geno-tools discover
```

```
geno-tools
── discover · 19 ───────────────────────────────
  Core Framework
    geno-audit     https://github.com/42euge/geno-audit.git
    geno-iso       https://github.com/42euge/geno-iso.git
  Developer Tools
    geno-loops     ✓ installed
    geno-dev       https://github.com/42euge/geno-dev.git
  ...
```

## 4. Install a skillset

```bash
geno-tools install geno-loops                              # from the registry
geno-tools install https://github.com/42euge/geno-loops.git  # any git URL
```

Clones, creates a venv, registers skills with your agents, resolves
dependencies. Untrusted sources (external URLs) are audited first. Skills
appear as `/geno-loops-…` slash commands.

## 5. Status

```bash
geno-tools status
```

```
geno-tools
── installed · 2 ───────────────────────────────
  geno-loops  0.2.0  main@94eba89  ● in-sync
  geno-notes  0.1.0  main@5f3fb1f  ▼ behind e84fa17
```

```bash
geno-tools upgrade            # update skillsets
geno-tools remove <name>      # uninstall one
brew upgrade geno-tools       # update geno-tools itself
```
