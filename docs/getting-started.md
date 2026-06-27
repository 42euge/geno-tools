# Getting Started

`geno-tools` is the meta package manager for the geno-* skill ecosystem. You
install it once as a plugin in your coding agent; it then discovers, installs,
and manages every other skillset.

Supported agents: **Claude Code**, **Codex**, **Antigravity CLI**.

## 1. Install the plugin

=== "Claude Code"

    Inside a Claude Code session:

    ```text
    /plugin marketplace add 42euge/geno-tools
    /plugin install geno-tools@geno-tools
    /reload-plugins
    ```

    Verify with `/plugin list` — you should see `geno-tools` enabled.

=== "Codex"

    ```text
    /plugin marketplace add 42euge/geno-tools
    /plugins        # pick "geno-tools", enable it
    ```

=== "Antigravity CLI"

    ```bash
    agy plugin install https://github.com/42euge/geno-tools
    ```

## 2. Install the CLI

The plugin tries to put the `geno-tools` command on your PATH automatically, but
that can fail silently (e.g. when `pipx` isn't found). Run the setup skill to do
it loudly and reliably:

```text
/geno-tools-setup
```

It installs the CLI via `pipx` (installing `pipx` itself if missing) and reports
the result. Then confirm:

```bash
geno-tools --version
```

If it's still not found, the skill prints the exact PATH fix; details land in
`~/.geno/bootstrap.log`.

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

Clones it, sets up an isolated venv, registers its skills with every agent, and
pulls in any dependencies automatically. Its skills then appear as slash
commands (e.g. `/geno-loops-...`).

You can also install directly by git URL — useful for private repos discovery
won't see:

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

Update what's behind with `geno-tools update` (one skillset, or all). Remove one
with `geno-tools remove <name>`.
