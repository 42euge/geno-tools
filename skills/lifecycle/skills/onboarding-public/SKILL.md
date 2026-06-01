---
name: geno-lifecycle-onboarding-public
description: >-
  Onboard a user's `geno-*` repo into the curated public registry. Either
  discover existing `geno-*` repos under the user's GitHub account, or guide
  them through creating one from scratch. Use when the user wants to publish
  a public `geno-*` skillset, find which of their repos already qualify, or
  bootstrap their first one.
allowed-tools: "Bash(*) Read Write Edit"
---

# geno-lifecycle-onboarding-public — Public Registry Onboarding

Helps an individual user get a `geno-*` repo into the curated public registry so any `geno-tools` install can resolve it by name.

The skill has two entry points depending on what the user already has:

1. **Discover** — scan the user's GitHub account for existing `geno-*` repos and surface candidates ready to admit.
2. **Create** — bootstrap a brand-new `geno-*` repo if they don't have one yet, then admit it.

For internal/private skillsets that live behind an enterprise git host, use the sibling [`/geno-lifecycle-onboarding-enterprise`](../onboarding-enterprise/SKILL.md) skill instead.

## When to invoke

- The user says "publish my skillset" / "get my repo into the registry".
- The user says "do I already have a geno-* repo?" / "what would qualify?" — they want to discover candidates.
- The user says "I want to start a new geno-* skillset" — they need a scaffold first.
- A reviewer is preparing the registry PR and wants the audit checklist walked.

## Decide: discover or create

Open with one question: *"Do you already have a `geno-*` repo on GitHub, or do we need to start one from scratch?"* The answer routes to one of the two branches below.

If the user is unsure, run the **Discover** branch first — it's read-only and tells you whether anything exists.

## Branch A — Discover the user's existing repos

When the user has (or might have) `geno-*` repos already on GitHub:

1. **Confirm the GitHub identity**. Ask for the username/org. Default to whatever `gh auth status` reports if available.
2. **Configure a discovery source**. Edit `~/.geno/config.yaml` to add (or confirm) a public-GitHub source pointed at the user's account:

   ```yaml
   discovery:
     sources:
       - kind: github
         org: <github-username>
         prefix: geno-
   ```

   No `base_url` / no `auth_env` — public github.com works without a token (subject to rate limits; if hit, set `auth_env: GITHUB_TOKEN`).
3. **Run discovery dry-run**. `"$CLAUDE_PLUGIN_ROOT/skills/lifecycle/skills/onboarding-enterprise/resources/discover.sh" --dry-run` lists matching candidates without installing.
4. **Filter to qualifying repos**. A candidate qualifies for the public registry when:
   - Repo name matches `geno-*`.
   - Has `SKILL.md` at the repo root.
   - Repository is public (or about to be).
5. **Pick one**. If the user has multiple, ask which one they want to onboard first. Then continue with the admit flow below.

If discovery surfaces zero candidates, fall through to **Branch B**.

## Branch B — Create a new `geno-*` repo

When the user has no qualifying repo yet:

1. **Pick a slug**. Confirm the bare name (e.g. `geno-foo`). Bare slug = single-word noun describing the domain. Reject anything that already exists under their GitHub account or in the public registry.
2. **Scaffold the repo**. Hand off to `/geno-lifecycle-repo-create` (or invoke its resource script). It generates the directory tree, manifest, docs scaffold, and CI templates — including the `SKILL.md` + `skills/` shape the registry expects.
3. **Push to a public remote**. `git push -u origin main`. The repo must be public for the registry path to make sense; recommend the user flip the visibility now if it's still private.
4. **Continue with the admit flow**.

## Admit flow (after either branch)

Whichever branch produced the repo, finish with:

1. **Verify repo shape**. `git ls-tree -r --name-only HEAD` against the candidate. Confirm `SKILL.md` is at root and the repo name is `geno-*`. If they passed a URL, clone shallow into `/tmp/` first.
2. **Self-test locally**. `"$CLAUDE_PLUGIN_ROOT/skills/manager/skills/install/resources/install.sh" /path/to/local/checkout`. Confirm slash commands appear in the agent.
3. **Walk the audit checklist**. Read `docs/onboarding/audit.md` and walk it section-by-section — don't dump the whole thing.
4. **Open the registry PR**. Either:
   - Use the gh MCP to draft the PR adding `"<repo-name>": "<git-url>"` to `skills/geno-tools/lib/registry.sh`, or
   - Print the patch (a single line addition keyed by repo name) for the user to apply.
5. **Log the audit decision** in the PR description. Don't sign off if the audit checklist has open red flags.
6. **After merge**, `geno-tools install <repo-name>` works for everyone.

## Don'ts

- Don't add tokens or other secrets to the registry — it's a public file.
- Don't admit a repo that's still private; the registry assumes public access.
- Don't skip the audit even for "trusted" authors. The checklist exists for the few times that trust is misplaced.
- Don't repurpose this skill for enterprise/private namespaces — those need discovery sources keyed to a `{slug}-` prefix and a different audit owner. Use [`/geno-lifecycle-onboarding-enterprise`](../onboarding-enterprise/SKILL.md).

## See also

- `docs/onboarding/index.md` — full onboarding flow
- `docs/onboarding/audit.md` — reviewer checklist
- `skills/geno-tools/lib/registry.sh` — the public registry being edited
- `skills/lifecycle/skills/onboarding-enterprise/resources/discover.sh` — shared discovery dry-run script (used by Branch A)
- `/geno-lifecycle-repo-create` — repo scaffold (used by Branch B)
