# geno-tools

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/geno-tools/)

The manifest-driven compiler ("Yocto for Skills") for AI agent environments.

**Website:** <https://42euge.github.io/geno-tools>

## What it does

`geno-tools` solves the problem of restricting AI agents from using the wrong tools or MCPs. It acts as the "one plugin to rule them all". You describe an environment in a manifest (`geno-image.yaml`), and `geno` compiles a strict, customized environment (`build/`) that you load into your agent.

If a skill is not explicitly included in the manifest (or if it's explicitly excluded), it doesn't get baked into the final output. The AI is physically restricted from accessing it.

Every bake is:

- **Audited** — a built-in compliance scan checks every skill file for curl-pipe-sh installs, prompt-injection phrasing, credential access, destructive commands, and over-broad tool grants. Error findings block the bake unless explicitly allowlisted; the full report lands in `build/audit-report.json`.
- **Reproducible** — `geno-image.lock` records layer sources, git commits, and per-skill content hashes. Two bakes of the same inputs are byte-identical, and the builder warns when the environment drifts from the last bake.
- **Agent-agnostic** — the build emits adapter manifests for Claude Code, Codex, Cursor, OpenCode, Gemini CLI, and Antigravity, selectable per environment.

## The Workflow

1. **Run the interactive builder** (the primary interface):

   ```bash
   npm link   # once
   geno
   ```

   Pick skill layers (grouped by ecosystem), pick skills — each shows its description and an inline audit glyph (`✓` clean, `⚠` warnings, `✗` blocking findings; press `a` for details, `/` to filter) — choose which agents to target, and bake. Your choices are saved to `geno-image.yaml`.

2. **Or edit the manifest directly** and bake headless (scripts, CI):

   ```yaml
   name: "geno-strict-env"
   version: "1.0.0"

   layers:
     - ./layers/meta-geno-core
     - https://github.com/some-org/custom-skill-layer

   install:
     - core/geno-audit
     - core/geno-tools

   exclude:
     - dangerous-eval-skill

   targets:
     - claude
     - generic
   ```

   ```bash
   geno bake     # or: npm run bake
   ```

3. **Install the single compiled plugin into your agent:**

   ```bash
   # Antigravity CLI
   agy plugin install ./build

   # Claude Code
   /plugin install ./build
   ```

## Project structure

```
.
├── GENO.md             # agent-facing canonical guidance
├── geno-image.yaml     # default environment manifest
├── geno-image.lock     # reproducibility lockfile
├── layers/             # source layers (meta-geno-core ships the built-in skills)
├── bin/                # geno CLI + interactive builder
├── lib/                # the compiler (manifest, layers, audit, lockfile, adapters)
├── test/               # node:test suite — `npm test`
├── docs/               # MkDocs Material docs
└── GEMINI.md, AGENTS.md, CLAUDE.md
```

## Development

```bash
npm test        # zero-dependency test suite (node:test)
```

## License

MIT
