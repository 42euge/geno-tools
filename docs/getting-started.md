# Getting Started

`geno-tools` is the meta package manager for the geno-* skill ecosystem. Install
it once as a plugin in your coding agent; it then installs and manages every
other skillset.

It currently supports **Claude Code**, **Codex**, and **Antigravity CLI**.

## Install

=== "Claude Code"

    Run inside a Claude Code session:

    ```text
    /plugin marketplace add 42euge/geno-tools
    /plugin install geno-tools@geno-tools
    ```

    The `SessionStart` hook bootstraps `~/.geno/` and puts the `geno-tools`
    command on your PATH automatically. Verify with `/plugin list`.

=== "Codex"

    Run inside a Codex session, then bootstrap once from your shell:

    ```bash
    /plugin marketplace add 42euge/geno-tools
    /plugins        # pick "geno-tools" and enable it
    ```
    ```bash
    bash ~/.codex/plugins/cache/geno-tools/geno-tools/*/geno_tools/scripts/bootstrap.sh
    ```

=== "Antigravity CLI"

    ```bash
    agy plugin install https://github.com/42euge/geno-tools
    bash ~/.gemini/antigravity-cli/plugins/geno-tools/geno_tools/scripts/bootstrap.sh
    ```

## Verify

```bash
geno-tools ls --available
```

If `geno-tools` isn't found, the bootstrap couldn't reach `pipx`. Install it and
re-run the bootstrap:

```bash
python3 -m pip install --user pipx
# then re-run the bootstrap.sh line for your agent above
```

Check `~/.geno/bootstrap.log` if it still fails.

## First steps

```bash
geno-tools ls --available     # see installable skillsets
geno-tools install geno-dev   # install one (clones, registers its skills)
geno-tools ls                 # what you have installed
```

That's it — installed skillsets surface their skills as slash commands in your
agent.
