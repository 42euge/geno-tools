# Getting Started

Supported agents: **Claude Code**, **Codex**, **Antigravity CLI**.

## 1. Install the CLI

```bash
brew install 42euge/geno/geno
```

The tap ships a single umbrella formula named **`geno`** (not `geno-tools`) —
it pipx-installs `geno-tools` and the other geno CLIs for you. CLI only; no
agent is touched. All state lives in `~/.geno/`.

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
geno-tools remove <name>      # remove one skillset
brew upgrade 42euge/geno/geno # update geno-tools itself
```

Removing everything is one command — the inverse of install. It removes all
skillsets, agent registrations, and plugin clones, and always keeps your data
in `~/.geno`:

```bash
geno-tools uninstall --dry-run   # preview: what's removed vs KEPT
geno-tools uninstall             # do it (prompts to confirm)
pipx uninstall geno-tools        # last step: remove the CLI package itself
```

## 6. Define a profile

A [profile](profiles-and-launch.md) names the skills (at pinned variants) and
MCP servers a launched session should see — and nothing else.

```bash
geno-tools profile create eng --agent claude-code
```

Then edit `~/.geno/profiles/eng.yaml`:

```yaml
agents: [claude-code]
skills:
  - name: geno-loops
  - name: geno-notes
mcp: [core]
```

```bash
geno-tools profile show eng      # human-readable resolved view
geno-tools resolve eng           # the resolved plan as JSON
```

## 7. Launch a scoped session

```bash
geno-tools launch claude-code --profile eng .
```

This runs Claude Code inside an isolated container that sees only `eng`'s
skills and MCP servers. Add `--rm` for a one-shot, or `--dry-run` to preview
the invocation without starting anything. Requires Docker + the bundled
`geno-iso` runtime.
