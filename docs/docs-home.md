<div class="hero" markdown>

# geno-<span>tools</span>

The agent-agnostic skill catalog for AI coding agents.
Discover, absorb, govern, evolve — as a native plugin in any coding agent.

<div class="hero-buttons">
<a href="getting-started/" class="btn-primary">Get Started</a>
<a href="skills/" class="btn-secondary">Skill Catalog</a>
</div>

</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<span class="card-icon">:material-magnify:</span>

### Discover

Find skills from open-source repos, private mirrors, and compliant local skillset checkouts.

[Get started :material-arrow-right:](getting-started.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-download:</span>

### Absorb

Index external skill systems (Superpowers, Vercel Skills, Ralphy Loop) into a unified catalog format.

[Architecture :material-arrow-right:](architecture/index.md)
</div>

<div class="feature-card" markdown>
<span class="card-icon">:material-source-branch:</span>

### Evaluate

Compose and curate reusable skillsets for your team while maintaining onboarding standards.

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

Share and align skill workflows across teams and private namespaces.

[Ecosystem :material-arrow-right:](ecosystem.md)
</div>

</div>

<div class="quick-taste" markdown>

## Quick taste

=== "Claude Code"

    ```bash
    /plugin marketplace add 42euge/geno-tools
    /plugin install geno-tools@geno-tools

    /geno-tools-open-docs
    /geno-skills-status
    /geno-skills-install <path>
    ```

=== "Antigravity CLI"

    ```bash
    agy plugin install https://github.com/42euge/geno-tools
    /geno-tools-open-docs
    /geno-skills-status
    /geno-skills-install <path>
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
