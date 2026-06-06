# Getting Started

Prerequisites: Git, Node.js for `npx skills`, and Python 3.11+.

## Install

Install geno-tools in the coding agent you use. Claude Code and OpenCode run the bootstrap automatically; Antigravity CLI, Codex, and Cursor need the bootstrap once.

=== "Claude Code"
    ```text
    /plugin marketplace add 42euge/geno-tools
    /plugin install geno-tools@geno-tools
    ```

=== "Antigravity CLI"
    ```bash
    agy plugin install https://github.com/42euge/geno-tools
    bash ~/.gemini/antigravity-cli/plugins/geno-tools/scripts/bootstrap.sh
    ```

=== "Codex CLI"
    ```text
    /plugin marketplace add 42euge/geno-tools
    /plugins
    ```

    ```bash
    bash ~/.codex/plugins/cache/geno-tools/geno-tools/*/scripts/bootstrap.sh
    ```

Verify from inside your agent:

```text
/geno-tools ls --available
```

## Install a skillset

List available skillsets, then install one:

```text
/geno-tools ls --available
/geno-tools install geno-<name>
```

This clones the repo, prepares any declared venvs, and registers the skill commands in your agent.

Check installed skillsets:

```text
/geno-tools ls
```

## Develop locally

Link a local checkout instead of cloning:

```text
/geno-tools dev geno-<name> ~/src/geno-<name>
```

Edits take effect immediately.

## What's next?

- [CLI Reference](cli-reference.md) — full command documentation
- [Creating a Skillset](skillsets/creating.md) — build your own
- [Variants & Worktrees](architecture/variants.md) — experiment with `fork` and `use`
