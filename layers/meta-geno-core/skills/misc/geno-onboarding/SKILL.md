---
name: geno-onboarding
description: >-
  Walks an operator through onboarding a new skillset into a geno-tools install,
  including enterprise discovery from GitHub Enterprise, GitLab, Bitbucket, or
  Gitea. Use when the user wants to add a new skillset, set up a private
  namespace, or audit a candidate repo before installing.
allowed-tools: "Bash(geno-tools *) Bash(python3 -m genotools *) Read Write Edit"
---

# geno-onboarding — Skillset Onboarding (Public + Enterprise)

Helps an operator onboard a new skillset to their geno-tools install. Two flavors:

1. **Public** — adding a `geno-*` repo to the curated registry.
2. **Enterprise** — admitting a `{company-slug}-*` repo into a private namespace, optionally via auto-discovery against GitHub Enterprise / GitLab / Bitbucket / Gitea.

## When to invoke

- The user says "onboard a skillset" / "add a new geno repo" / "wire up our internal skillset".
- The user wants `geno-tools` to discover repos in their company's git host.
- The user is preparing an audit before installing an unfamiliar skillset.
- A platform team is bootstrapping a new private namespace.

## Public onboarding flow

```
1. Verify repo shape       → SKILL.md + commands/ at root, optional skills/<sub>/SKILL.md
2. Self-test locally       → geno-tools dev <repo-name> ~/src/<repo-name>
3. Push to a public remote → git push -u origin main
4. Register                → PR adding "<repo-name>": "<git-url>" to genotools/registry.py
5. Audit                   → docs/onboarding/audit.md checklist
6. Merge → install         → geno-tools install <repo-name>
```

## Enterprise onboarding flow

```
1. Pick a namespace        → {company-slug}-* (e.g. acme-finance, acme-incident-response)
2. Mirror the skillset spec → identical SKILL.md + commands/ + optional venv layout
3. Host privately          → GitHub Enterprise / GitLab / Bitbucket / Gitea
4. Configure discovery     → ~/.geno/config.yaml → discovery.sources
5. Audit                   → docs/onboarding/audit.md (run by platform team)
6. Install                 → geno-tools install <repo-name>  (resolved via discovery)
```

## Discovery configuration

Edit `~/.geno/config.yaml` to declare where to look for candidate skillsets. Every source is queried by `geno-tools ls --available` and `geno-tools install <repo>`.

```yaml
discovery:
  sources:
    - kind: github
      org: 42euge

    - kind: github
      org: acme-corp
      base_url: https://github.acme.com/api/v3
      prefix: acme-
      auth_env: ACME_GITHUB_TOKEN

    - kind: gitlab
      group: platform/skillsets
      base_url: https://gitlab.acme.com
      prefix: acme-
      auth_env: ACME_GITLAB_TOKEN
```

**Common fields**
- `kind` — provider (`github`, `gitlab`, `gitea`, `bitbucket`)
- `prefix` — only repos whose name starts with this prefix are candidates (e.g. `geno-`, `acme-`)
- `base_url` — for self-hosted instances; omit for public github.com / gitlab.com
- `auth_env` — environment variable name holding a token; never paste the token itself

**A repo is a candidate when:**
1. Its name matches `{prefix}<something>` (e.g. starts with `acme-`).
2. It has a `SKILL.md` at the repo root.
3. The platform team has signed off on the audit (enterprise only).

Repos that don't match are silently ignored — discovery never auto-installs anything; it only surfaces candidates.

## Walking the operator through it

When the user invokes this skill:

1. **Identify the goal**. Ask whether this is public-registry onboarding or enterprise. If unclear, ask once.
2. **Inspect the repo**. Run `git ls-tree -r --name-only HEAD` against the candidate repo and confirm `SKILL.md` is at root. If they pass a URL, clone shallow into `/tmp/` first.
3. **Surface the audit checklist**. Read `docs/onboarding/audit.md` and walk the checklist with the user, capturing answers. Don't just dump it — ask one section at a time.
4. **For enterprise discovery**: open `~/.geno/config.yaml`, add or update the `discovery.sources` block, validate the YAML, and verify the auth env var is set in the operator's shell.
5. **Dry-run discovery**. `geno-tools discover --dry-run` lists candidates without installing.
6. **Decide**. Either:
   - Public: open the registry PR (use the gh MCP if available, or print the patch for the user to apply).
   - Enterprise: add to the internal manifest / forked registry / leave to direct URL.
7. **Verify by installing**. `geno-tools install <repo-name>`. Confirm slash commands appear in the agent.

Always log the audit decision somewhere durable (PR description, internal ticket, or platform-team doc). Don't sign off if the audit checklist has open red flags.

## Don'ts

- Don't paste tokens into `config.yaml`. Use `auth_env` and a secrets manager.
- Don't modify `genotools/registry.py` for an enterprise skillset — that's the public registry. Use discovery sources or a forked registry instead.
- Don't bypass the audit, even for "trusted" internal authors. The checklist exists for the few times that trust is misplaced.
- Don't auto-install everything discovery surfaces. Discovery only proposes; the operator (or the platform team) approves.

## See also

- `docs/onboarding/index.md` — full onboarding flow
- `docs/onboarding/audit.md` — reviewer checklist
- `genotools/discovery.py` — the pluggable provider layer
