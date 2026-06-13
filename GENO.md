# geno-tools — The Yocto of AI Skills

`geno-tools` is a manifest-driven compiler that generates strict, custom agent environments. It acts as the *only* plugin an agent needs to load.

@./VISION.md
@./TENETS.md

## The Workflow

Agents do not load `geno-tools` directly from its root. Instead, you describe an environment in a manifest (`geno-image.yaml`), compile it into a `build/` directory, and point the agent at `build/`. The primary interface is the interactive builder; `geno bake` is its headless twin for scripts and CI.

### 1. The Interactive Builder (primary)

```bash
npm link        # once, to get the global `geno` command
geno            # launches the interactive environment builder
```

The TUI walks through: select skill layers (grouped by ecosystem) → choose install mode → pick skills (with frontmatter descriptions, audit glyphs, `/` type-to-filter, `a` for audit details and allowlisting) → choose agent targets → save manifest and bake. On launch it shows a drift banner when skills changed since the last bake.

### 2. The Manifest (`geno-image.yaml`)

```yaml
name: "geno-strict-env"
version: "1.0.0"

layers:
  - ./layers/meta-geno-core          # local layer
  # - https://github.com/org/layer   # remote layers are cloned into .geno-bake-cache/

install:
  - core/geno-tools                  # ids are <category>/<name> under <layer>/skills/
  - core/geno-audit

exclude:
  - geno-dangerous-skill             # matches full id or bare skill name

targets:                             # adapter manifests to emit (omit = all)
  - claude
  - generic

audit:
  allow:                             # allowlist intentional audit findings
    - misc/geno-tools-update:curl-pipe-sh
```

### 3. Baking (headless)

```bash
geno bake       # or: npm run bake
```

Every bake runs the pipeline: validate manifest → resolve layers → **audit every skill file** (error findings block the bake unless allowlisted; report at `build/audit-report.json`) → copy skills (later layers override earlier ones) → emit per-agent adapter manifests → write `geno-image.lock` (deterministic content hashes; commit it for reproducible environments).

### 4. Agent Usage

The agent MUST use the compiled output:

```bash
agy plugin install ./build     # Antigravity
/plugin install ./build        # Claude Code / Codex
```

The bake summary prints the install command for every selected target.

## Ecosystem Taxonomy

The `geno` skill universe is organized into the following strict ecosystem categories. Each skill repository MUST include a `layer.json` declaring its ecosystem assignment.

* **geno-ecosystem / Core Framework**: The foundational architecture, execution engines, and standards. (`geno-cli`, `geno-meta`, `geno-specs`, `geno-audit`, `geno-iso`)
* **geno-ecosystem / Workspaces & Data**: Tools for managing context, state, and knowledge bases. (`geno-ws`, `geno-mine`, `geno-notes`)
* **geno-ecosystem / Developer Tools**: The infrastructure for testing, debugging, and monitoring agents. (`geno-dev`, `geno-bench`, `geno-mon`, `geno-loops`)
* **geno-ecosystem / Modalities & Capabilities**: Advanced skills that give agents new senses or execution models. (`geno-agents`, `geno-vla`, `geno-voice`, `geno-media`)
* **geno-ecosystem / Applied Research**: Domain-specific problem-solving environments. (`geno-research`, `geno-kaggle`)
* **geno-ecosystem / Interfaces & Comms**: How the agent interacts with the user and other systems. (`geno-term`, `geno-msg`, `geno-notify`, `geno-camp`)

## Repo structure

```
geno-tools/
├── GENO.md                        # agent instructions (this file)
├── geno-image.yaml                # default manifest
├── geno-image.lock                # reproducibility lockfile (committed)
├── layers/                        # Source skill/tool layers
│   └── meta-geno-core/            # The default built-in skills
│       ├── layer.json
│       └── skills/<category>/<name>/SKILL.md
├── bin/
│   ├── geno.js                    # CLI entry: tui | bake | init | help
│   └── tui.js                     # the interactive environment builder
├── lib/                           # the compiler
│   ├── yaml.js                    # strict YAML-subset parser/serializer
│   ├── manifest.js                # load/validate geno-image.yaml
│   ├── layers.js                  # layer resolution, skill discovery, frontmatter
│   ├── audit.js                   # compliance rules (gates every bake)
│   ├── lockfile.js                # deterministic lock + drift detection
│   ├── adapters.js                # per-agent build output emitters
│   └── bake.js                    # pipeline orchestration
├── test/                          # node:test suite (`npm test`)
├── docs/                          # MkDocs documentation
└── LICENSE                        # MIT license
```

## Adding a new skill to the Core Layer

To add a built-in skill:

1. Add `layers/meta-geno-core/skills/<category>/<name>/SKILL.md` (frontmatter must declare `name`, `description`, and a scoped `allowed-tools` — the audit warns on missing or `Bash(*)` grants).
2. Add `<category>/<name>` to `geno-image.yaml` under `install`.
3. Re-run `geno bake` (commit the updated `geno-image.lock`).
