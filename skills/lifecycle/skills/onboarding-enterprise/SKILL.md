---
name: geno-lifecycle-onboarding-enterprise
description: >-
  Onboard an enterprise namespace into geno-tools. Either discover existing
  `{company-slug}-*` prefixes already in use (configured discovery sources or
  enterprise org scans), or guide a platform team through picking a new
  prefix and bootstrapping the first repo. Supports GitHub Enterprise,
  GitLab, Bitbucket, Gitea. Use when wiring up an internal skillset, finding
  what's already in use across the company, or standing up a brand-new
  private namespace.
allowed-tools: "Bash(*) Read Write Edit"
---

# geno-lifecycle-onboarding-enterprise — Enterprise Namespace Onboarding

Helps a platform team or operator wire up a `{company-slug}-*` namespace into a `geno-tools` install.

The skill has two entry points depending on whether the namespace already exists:

1. **Discover** — find enterprise prefixes already in use (in `~/.geno/config.yaml` or by scanning the enterprise git host) and surface candidate repos.
2. **Create** — guide a platform team through picking a new `{slug}-*` prefix, scaffolding the first repo, and configuring discovery so the rest of the company can resolve it.

For an individual user adding a `geno-*` repo to the public registry, use the sibling [`/geno-lifecycle-onboarding-public`](../onboarding-public/SKILL.md) skill instead.

## When to invoke

- The user says "wire up our internal skillset" / "onboard an enterprise skillset".
- The user says "what enterprise prefixes do we already have?" / "do we use geno-tools internally yet?" — they want to discover.
- A platform team is bootstrapping a new private namespace for the first time.
- The user is preparing an audit before installing an unfamiliar internal skillset.

## Decide: discover or create

Open with: *"Is there already a `{slug}-*` namespace in use at your company, or are we standing up a new one?"* If the user is unsure, run the **Discover** branch first — it's read-only and tells you whether anything is already configured or detectable.

## Branch A — Discover existing enterprise prefixes

When the user thinks (or wants to check whether) a namespace is already in use:

1. **Read existing config**. Open `~/.geno/config.yaml` and list every entry under `discovery.sources`. Surface each `prefix:` and `org:` / `group:` / `base_url:` so the user can see which namespaces are already wired up.
2. **Dry-run each configured source**. `"$CLAUDE_PLUGIN_ROOT/skills/lifecycle/skills/onboarding-enterprise/resources/discover.sh" --dry-run` lists candidates without installing. Group output by source.
3. **If nothing's configured, scan to propose**. Ask the user for the enterprise git host (`https://github.acme.com`, `https://gitlab.acme.com`, etc.) and a token env var. Add a tentative source with `prefix: ""` and dry-run `discover.sh` — repos matching `*-*` patterns are prefix candidates. Tally the most common prefix; that's likely the one in use.
4. **Confirm and lock the prefix**. Once the user picks one, update `~/.geno/config.yaml` to set the canonical `prefix:` for that source. Re-run discovery to confirm only the intended repos surface.
5. **Pick the candidate to onboard** (or move to the per-repo audit flow below).

If the prefix doesn't exist yet, fall through to **Branch B**.

## Branch B — Create a new enterprise prefix

When the namespace is new and needs to be designed:

1. **Pick the prefix**. Walk the platform-team contact through choosing a `{company-slug}-` prefix. Rules:
   - Lowercase, hyphen-separated, namespaces the company uniquely.
   - Avoid generic words — `corp-`, `internal-` collide too easily across orgs.
   - Reserve room for sub-namespaces: `acme-` is fine; `acme-finance-` overcommits.
2. **Pick the host**. GitHub Enterprise / GitLab self-hosted / Bitbucket / Gitea. Confirm the operator has admin rights to create repos under the host.
3. **Scaffold the first repo**. Hand off to `/geno-lifecycle-repo-create` to generate `{slug}-foo` — directory tree, manifest, docs scaffold, CI. This becomes the reference shape for everyone else in the namespace.
4. **Configure discovery** in `~/.geno/config.yaml`:

   ```yaml
   discovery:
     sources:
       - kind: github          # or gitlab / bitbucket / gitea
         org: acme-corp
         base_url: https://github.acme.com/api/v3
         prefix: acme-
         auth_env: ACME_GITHUB_TOKEN
   ```

   Validate the YAML. Verify the auth env var is set in the operator's shell (`echo "${ACME_GITHUB_TOKEN:?}"`).
5. **Document for the team**. Capture the prefix, host, and audit owner in the platform-team's runbook so future authors don't redo this work.
6. **Continue with the admit flow** for the first repo (and any later repos in the namespace).

## Discovery configuration reference

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
- `prefix` — only repos whose name starts with this prefix are candidates
- `base_url` — for self-hosted instances; omit for public github.com / gitlab.com
- `auth_env` — environment variable name holding a token; never paste the token itself

**A repo is a candidate when:**
1. Its name matches `{prefix}<something>`.
2. It has a `SKILL.md` at the repo root.
3. The platform team has signed off on the audit.

Repos that don't match are silently ignored — discovery never auto-installs anything; it only surfaces candidates.

## Admit flow (after either branch)

Whichever branch produced the candidate repo, finish with:

1. **Inspect the repo**. `git ls-tree -r --name-only HEAD` and confirm `SKILL.md` is at root. If they pass a URL, clone shallow into `/tmp/` first.
2. **Walk the audit checklist**. Read `docs/onboarding/audit.md` and walk it section-by-section, capturing answers — don't just dump it.
3. **Decide on registration**. Either add the repo to an internal manifest / forked registry, or leave it as a direct URL install resolved via discovery.
4. **Verify by installing**. `"$CLAUDE_PLUGIN_ROOT/skills/manager/skills/install/resources/install.sh" <repo-name>`. Confirm slash commands appear in the agent.

Always log the audit decision somewhere durable (internal ticket, platform-team doc). Don't sign off if the audit checklist has open red flags.

## Don'ts

- Don't paste tokens into `config.yaml`. Use `auth_env` and a secrets manager.
- Don't modify `skills/geno-tools/lib/registry.sh` for an enterprise skillset — that's the public registry. Use discovery sources or a forked registry instead.
- Don't pick a generic prefix (`corp-`, `internal-`, `team-`) — it collides too easily across orgs.
- Don't bypass the audit, even for "trusted" internal authors. The checklist exists for the few times that trust is misplaced.
- Don't auto-install everything discovery surfaces. Discovery only proposes; the operator (or the platform team) approves.

## See also

- `docs/onboarding/index.md` — full onboarding flow
- `docs/onboarding/audit.md` — reviewer checklist
- `skills/geno-tools/lib/discovery.sh` — the pluggable provider layer
- `resources/discover.sh` — list candidate skillset repos from configured discovery sources
- `resources/scan.sh` — scan discovery sources and queue uninstalled candidates
- `/geno-lifecycle-repo-create` — repo scaffold (used by Branch B for the first namespace repo)
