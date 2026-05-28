---
title: geno-iso-credentials-extract
description: Refresh host credentials used for geno-iso container auth
---

# geno-iso-credentials-extract

`/geno-iso-credentials-extract`

> Refresh host credentials used for geno-iso container auth

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

1. For Claude, run `geno-iso creds --agent claude`
2. This reads the macOS Keychain entry `Claude Code-credentials` and writes `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_OAUTH_REFRESH_TOKEN`, and `CLAUDE_CODE_OAUTH_SCOPES` to `.env`
3. For Codex, run `geno-iso creds --agent codex`
4. This syncs host `~/.codex/auth.json` and `~/.codex/config.toml` for container seeding
5. Re-run the appropriate command if container auth fails

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-iso](index.md)
