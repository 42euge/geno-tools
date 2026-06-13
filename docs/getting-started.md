# Getting Started

`geno-tools` is a manifest-driven compiler for AI agent environments. You don't install this repo into your agent — you **bake** an environment from it and install the compiled `build/` output.

## 1. Get the `geno` command

```bash
git clone https://github.com/42euge/geno-tools
cd geno-tools
npm link        # makes `geno` available globally (zero dependencies)
```

## 2. Build your environment interactively

```bash
geno
```

The interactive builder walks you through the whole flow:

1. **Select skill layers** — local layers under `./layers/` plus any layers in your manifest, grouped by ecosystem. Remote layers can be discovered from GitHub via an explicit menu entry (no network calls happen unless you ask).
2. **Pick skills** — every skill shows its description from `SKILL.md` frontmatter and an inline audit glyph: `✓` clean, `⚠ n` warnings, `✗ n` blocking findings. Press `a` on a skill to see the findings and optionally allowlist it; press `/` to type-to-filter.
3. **Choose agent targets** — which adapter manifests the build emits (Claude Code, Codex, Cursor, OpenCode, Gemini CLI, Antigravity).
4. **Save & Bake** — your choices are written to `geno-image.yaml`, then compiled to `build/`.

If skills changed on disk since your last bake, the builder shows a drift banner on launch so you know `build/` is stale.

## 3. Or bake headless (scripts, CI)

```bash
geno init       # create a starter geno-image.yaml
geno bake       # validate → audit → compile → lock
```

The bake fails (exit 1) on manifest errors, missing skills, or blocking audit findings — making it safe to wire into CI.

## 4. Install the compiled environment

=== "Claude Code"

    ```text
    /plugin install ./build
    ```

=== "Antigravity CLI"

    ```bash
    agy plugin install ./build
    ```

=== "Codex"

    ```text
    /plugin install ./build
    ```

=== "OpenCode"

    The build ships a plugin shim at `build/.opencode/plugins/`. Point your OpenCode plugin path at `./build`.

=== "Cursor"

    Install `./build` via Cursor's plugin manager (it reads `build/.cursor-plugin/plugin.json`).

=== "Gemini CLI"

    ```bash
    gemini extensions install ./build
    ```

## What you get

- `build/skills/` — exactly the skills you installed, nothing else
- `build/audit-report.json` — every compliance finding, including allowlisted ones
- `build/.claude-plugin/`, `build/.codex-plugin/`, … — adapter manifests for your chosen targets
- `geno-image.lock` — deterministic content hashes for reproducible environments (commit this)

See the [CLI Reference](cli-reference.md) for the manifest schema, audit rules, and lockfile details.
