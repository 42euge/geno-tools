# geno-tools

Meta-CLI for installing and managing [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skillsets in the **geno-\*** ecosystem.

---

## What is it?

`geno-tools` is a package manager for Claude Code skills. Each skill lives in its own `geno-{name}` repo with a declarative manifest. geno-tools handles cloning, venvs, symlinks, variant management, and wiring skills into your agent of choice.

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Install in seconds**

    ---

    One `pipx install` and you're ready to add skillsets.

    [:octicons-arrow-right-24: Getting Started](getting-started.md)

-   :material-console:{ .lg .middle } **Full CLI reference**

    ---

    `ls`, `install`, `dev`, `fork`, `use`, `promote`, `update`, `remove`, `doctor`.

    [:octicons-arrow-right-24: CLI Reference](cli-reference.md)

-   :material-puzzle:{ .lg .middle } **Skillset ecosystem**

    ---

    Media, research, taxes, kaggle, agents — each a self-contained repo.

    [:octicons-arrow-right-24: Skillsets](skillsets/index.md)

-   :material-cog:{ .lg .middle } **Architecture**

    ---

    Disk layout, variant worktrees, target adapters.

    [:octicons-arrow-right-24: Architecture](architecture/index.md)

</div>

## Quick taste

```bash
pipx install git+https://github.com/42euge/geno-tools

geno-tools ls --available        # see the registry
geno-tools install media         # install geno-media
geno-tools fork media exp-1      # branch a variant
geno-tools use media@exp-1       # activate it
geno-tools promote media exp-1   # merge back to main
```

## Design principles

- **One manifest** — each skillset declares everything in `genotools.yaml`
- **Isolated by default** — per-skillset venvs, git worktrees for variants
- **Exact removal** — uninstall replays install in reverse, no orphaned files
- **Agent-agnostic** — target adapters for Claude Code today, Codex and Gemini CLI next
