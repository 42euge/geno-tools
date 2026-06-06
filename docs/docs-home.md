<div class="hero" markdown>

# geno-<span>tools</span>

The agent-agnostic meta package manager for AI coding agents.
Discover, absorb, evaluate, govern, evolve — as a native plugin in any coding agent.

<div class="hero-buttons">
<a href="getting-started/" class="btn-primary">Get Started</a>
<a href="skills/" class="btn-secondary">Skill Catalog</a>
</div>

</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<span class="card-icon">:material-magnify:</span>

### Discover

Find skills from open-source registries, private GitHub/GitLab orgs, or any git remote.

[Get started :material-arrow-right:](getting-started.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-download:</span>

### Absorb

Normalize external skill systems (Superpowers, Vercel Skills, Ralphy Loop) into a unified framework.

[Architecture :material-arrow-right:](architecture/index.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-source-branch:</span>

### Evaluate

Fork a skill, experiment in isolation, promote back to main. Git worktrees power the meta-harness.

[Variants :material-arrow-right:](architecture/variants.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-shield-check:</span>

### Govern

Built-in auditing scans for compliance — prompt injection, dependency hygiene, data boundaries.

[Audit process :material-arrow-right:](onboarding/audit.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-puzzle:</span>

### Evolve

Compose skills across agents, combine external innovation with private knowledge.

[Ecosystem :material-arrow-right:](ecosystem.md)
</div>

</div>

<div class="quick-taste" markdown>

## Quick taste

=== "Claude Code"

    ```bash
    /plugin marketplace add 42euge/geno-tools
    /plugin install geno-tools@geno-tools

    /geno-tools ls --available               # see the registry
    /geno-tools install geno-<name>          # install a skillset
    /geno-tools fork geno-<name> exp-1       # branch a variant
    /geno-tools use geno-<name>@exp-1        # activate it
    /geno-tools promote geno-<name> exp-1    # merge back to main
    ```

=== "Antigravity CLI"

    ```bash
    agy plugin install https://github.com/42euge/geno-tools
    bash ~/.gemini/antigravity-cli/plugins/geno-tools/scripts/bootstrap.sh

    /geno-tools ls --available               # see the registry
    /geno-tools install geno-<name>          # install a skillset
    /geno-tools fork geno-<name> exp-1       # branch a variant
    /geno-tools use geno-<name>@exp-1        # activate it
    /geno-tools promote geno-<name> exp-1    # merge back to main
    ```

</div>

## Design principles

:material-file-document-outline: **One manifest**
:   Each skillset declares everything in `genotools.yaml` — deps, scripts, configs.

:material-shield-lock-outline: **Isolated by default**
:   Per-skillset venvs. Git worktrees for variants. Nothing leaks.

:material-undo: **Exact removal**
:   Uninstall replays install in reverse. No orphaned files, ever.

:material-puzzle-outline: **Agent-agnostic**
:   Target adapters for Claude Code, geno-cli, Codex, and Antigravity CLI.

:material-sync: **Lifecycle-driven**
:   Every skill follows discover, absorb, evaluate, govern, evolve. The tooling enforces it.
