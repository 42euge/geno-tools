# CLI Reference

The `geno` command is a zero-dependency Node.js CLI. The interactive builder is the primary interface; everything else exists to support scripting and CI.

## Commands

| Command | Purpose |
|---------|---------|
| `geno` | Launch the interactive environment builder (default) |
| `geno bake` | Compile the environment from `geno-image.yaml`, headless |
| `geno init` | Create a starter `geno-image.yaml` |
| `geno help` | Show usage |

Exit codes: `0` success · `1` bake failure (manifest errors, missing skills, blocking audit findings) · `2` usage error.

## The interactive builder

Launched by bare `geno`. Keys:

| Key | Action |
|-----|--------|
| `TAB` / `↑` `↓` | Navigate |
| `ENTER` / `SPACE` | Toggle selection / activate button |
| `/` | Type-to-filter the skill list |
| `a` | Open audit details for the hovered skill (with one-key allowlisting) |
| `ESC` | Clear filter / back out / quit |

Skill rows show the description from `SKILL.md` frontmatter and an audit glyph: `✓` clean, `⚠ n` warnings, `✗ n` blocking findings. GitHub layer discovery is behind an explicit menu entry — the builder makes no network calls unless you ask.

## Manifest schema (`geno-image.yaml`)

```yaml
name: "geno-strict-env"        # build name (used in adapter manifests)
version: "1.0.0"

layers:                        # resolved in order; later layers override earlier
  - ./layers/meta-geno-core    # local path
  - https://github.com/org/x   # git URL, cloned to .geno-bake-cache/layers/

install:                       # skill ids: <category>/<name> under <layer>/skills/
  - core/geno-tools

exclude:                       # matches a full id or a bare skill name
  - geno-dangerous-skill

targets:                       # adapter outputs to emit; omit = all
  - claude                     # build/.claude-plugin/plugin.json
  - codex                      # build/.codex-plugin/plugin.json
  - cursor                     # build/.cursor-plugin/plugin.json
  - opencode                   # build/.opencode/plugins/<name>.js
  - gemini                     # build/gemini-extension.json
  - generic                    # build/plugin.json (read by Antigravity)

audit:
  allow:                       # allowlist intentional findings
    - misc/skill-name              # all rules for one skill
    - misc/skill-name:curl-pipe-sh # one rule for one skill
```

The parser is strict: unknown keys warn, malformed entries error with line numbers, and a typo'd key (e.g. `instal:`) is reported instead of producing a silently empty build.

## The audit gate

Every bake scans every file of every installed skill. There is no off switch — auditing gates every ingestion path by design. Findings land in `build/audit-report.json`.

| Rule | Severity | Catches |
|------|----------|---------|
| `curl-pipe-sh` | error | `curl … \| sh` style remote-code installs |
| `prompt-injection` | error | "ignore previous instructions", "do not tell the user", … |
| `credential-access` | error | SSH keys, `~/.aws/credentials`, keychain, `/etc/shadow` |
| `destructive` | error | `rm -rf /`, `chmod 777 /` |
| `exfil` | warn | base64-pipe-to-network, netcat listeners |
| `system-write` | warn | writes to `/etc`, `/usr`; `sudo` escalation |
| `broad-tools` | warn | missing `allowed-tools` frontmatter, or `Bash(*)` grants |

**Error** findings block the bake unless allowlisted in the manifest (`audit: allow:`). **Warn** findings print and pass. In the interactive builder, press `a` on any flagged skill to inspect findings and allowlist in place.

## The lockfile (`geno-image.lock`)

Written on every successful bake; commit it. Contains the manifest hash, each layer's source (and git commit for remote layers), and a sha256 content hash per installed skill. It has no timestamps — identical inputs produce a byte-identical lockfile — and powers the drift banner the builder shows when skills changed since the last bake.

## Skill slash commands

After installing a baked environment that includes them, these skills expose slash commands in the agent:

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| geno-tools | `/geno-tools` | Overview of the geno-tools skillset |
| geno-onboarding | `/geno-onboarding` | Walk an operator through skillset onboarding |
| geno-skills-install | `/geno-skills-install` | Register skills from a local checkout |
| geno-skills-create | `/geno-skills-create` | Scaffold a new SKILL.md in a repo |
| geno-skills-status | `/geno-skills-status` | Show installed skillset versions and status |
| geno-tools-update | `/geno-tools-update` | Update installed geno ecosystem skillsets |
| geno-tools-open-docs | `/geno-tools-open-docs` | Open this documentation site |
