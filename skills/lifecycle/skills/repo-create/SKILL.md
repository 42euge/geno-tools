---
name: geno-lifecycle-repo-create
description: >-
  Scaffold a new geno ecosystem skillset repo from scratch. Creates the full
  directory structure (genotools.yaml, GENO.md, CLAUDE.md, umbrella SKILL.md,
  docs, specs, CI) and initializes git. Use when user says
  /geno-lifecycle-repo-create, wants to create a new geno-* repo, or
  bootstrap a new skillset from scratch.
argument-hint: "[skillset-name|freeform description]"
allowed-tools: "Bash(*) Read(*) Write(*) Edit(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.2.0"
---

# geno-lifecycle-repo-create

Scaffolds a new `geno-{name}` skillset repo with the directory structure required by the geno ecosystem. This is the repo-level counterpart to [`/geno-lifecycle-skill-create`](../skill-create/SKILL.md), which adds skills to existing repos.

## Templates

The actual file contents live in three sibling docs, loaded only when needed during step 5:

- [`rules/repo-template.md`](rules/repo-template.md) — directory tree, `genotools.yaml`, `GENO.md`, `CLAUDE.md`, `.gitignore`, `README.md`, root `SKILL.md` symlink, umbrella skill, optional `pyproject.toml` and Python package.
- [`rules/ci-template.md`](rules/ci-template.md) — `.github/workflows/docs.yml` for GitHub Pages deploy, plus the post-push Pages enablement command.
- [`rules/docs-template.md`](rules/docs-template.md) — `mkdocs.yml`, `docs/index.md`, `docs/getting-started.md`, `docs/stylesheets/extra.css`, and the `.specs/` planning docs.

## When to invoke

- The user wants to create a brand new skillset repo (not add a skill to an existing repo).
- The user says "create a new geno repo", "bootstrap a skillset", "scaffold a new skillset".
- The user is starting a new domain of skills that doesn't fit any existing skillset.

## Input

`$ARGUMENTS` is either:
- A skillset name (e.g. `geno-pipelines`, `geno-career`) — skip naming, go straight to details
- Freeform text describing what the skillset should do — use it to derive the name
- Empty — launch the interactive flow

## Workflow

### 1. Determine the skillset name

If `$ARGUMENTS` contains a name matching `geno-*`, use it directly. Strip `geno-` to get the bare slug.

If `$ARGUMENTS` is freeform or empty, ask:
> What domain does this skillset cover? Give a short name (1-2 words, noun).
> Examples: pipelines, career, fitness, finance

Construct `geno-{slug}`. The slug must be lowercase, hyphen-separated if multi-word, a noun, and not already taken — check with `"$CLAUDE_PLUGIN_ROOT/skills/lifecycle/skills/install/resources/ls.sh" --available 2>/dev/null` and `ls ~/.geno-tools/`.

Record:
- `$NAME` — bare slug (e.g. `career`)
- `$REPO` — full repo name (e.g. `geno-career`)

### 2. Gather details

Use `AskUserQuestion`:
> Describe what this skillset does in 1-2 sentences.

From the answer, draft:
- `$DESCRIPTION` — one-line description for `genotools.yaml` and README
- `$LONG_DESCRIPTION` — opening paragraph for `GENO.md`
- `$TITLE` — title cased version of the name for headings

Confirm with the user before proceeding.

### 3. Choose optional features

Use `AskUserQuestion` (multiSelect):
> Which optional features should this skillset include?
> - **Python package** — adds `pyproject.toml` and a Python package directory
> - **Dependencies** — this skillset depends on other geno-* skillsets
> - **GitHub repo** — create the remote repo on GitHub after scaffolding

Record:
- `$HAS_PYTHON` — boolean
- `$DEPS` — list of dependency names (ask follow-up if selected)
- `$CREATE_REMOTE` — boolean

### 4. Determine target directory

- If inside a workspace (`.geno/.workspace/workspace.yaml` exists), scaffold inside the workspace root.
- Otherwise, scaffold in the current working directory.

The repo will be created at `$TARGET_DIR/$REPO/`. If it already exists, warn and ask whether to overwrite.

### 5. Render templates

Read the three rules files and render every template, substituting the variables collected in steps 1–3:

| Source | Targets |
|---|---|
| [`rules/repo-template.md`](rules/repo-template.md) | `genotools.yaml`, `GENO.md`, `CLAUDE.md`, `.gitignore`, `README.md`, `skills/$REPO/SKILL.md`, `SKILL.md` symlink, `pyproject.toml`+`${REPO_UNDERSCORE}/__init__.py` (if `$HAS_PYTHON`) |
| [`rules/ci-template.md`](rules/ci-template.md) | `.github/workflows/docs.yml` |
| [`rules/docs-template.md`](rules/docs-template.md) | `mkdocs.yml`, `docs/index.md`, `docs/getting-started.md`, `docs/stylesheets/extra.css`, `.specs/VISION.md`, `.specs/GOALS.md`, `.specs/TENETS.md`, `.specs/features/.gitkeep` |

Substitution variables (rendered into every file that mentions them):
- `$REPO` — full repo name (e.g. `geno-career`)
- `$NAME` — bare slug (e.g. `career`)
- `$DESCRIPTION` — one-line description
- `$LONG_DESCRIPTION` — paragraph
- `$TITLE` — heading-cased name
- `$DEPS` — list of dependency names (only consumed by `genotools.yaml`)
- `$REPO_UNDERSCORE` — `$REPO` with hyphens replaced by underscores (only consumed if `$HAS_PYTHON`)

The root `SKILL.md` symlink is created with `ln -s skills/$REPO/SKILL.md SKILL.md` (per `rules/repo-template.md`).

### 6. Initialize git

```bash
cd $TARGET_DIR/$REPO
git init
git add -A
git commit -m "Initial scaffold via /geno-lifecycle-repo-create"
```

### 7. Create GitHub remote (only if `$CREATE_REMOTE`)

```bash
gh repo create 42euge/$REPO --private --source . --push --description "$DESCRIPTION"
```

Default to `--private`. Ask if they want public instead. After push, enable GitHub Pages — see the post-push command in [`rules/ci-template.md`](rules/ci-template.md).

### 8. Report

```
Created $REPO at $TARGET_DIR/$REPO

Files: see rules/repo-template.md, rules/ci-template.md, rules/docs-template.md

Next steps:
  1. Add skills:        /geno-lifecycle-skill-create  (from inside the repo)
  2. Install locally:   "$CLAUDE_PLUGIN_ROOT/skills/lifecycle/skills/install/resources/install.sh" $TARGET_DIR/$REPO
  3. Audit compliance:  /geno-compliance-audit         (from inside the repo)
```

## Don'ts

- Don't use aliased prefixes like `gt-` in any generated content — always use canonical `geno-` prefix.
- Don't scaffold skills beyond the umbrella — use `/geno-lifecycle-skill-create` for that.
- Don't overwrite an existing repo directory without asking.
- Don't commit `.geno/` or `CLAUDE.local.md` in the initial commit.
- Don't create `GEMINI.md` or `AGENTS.md` — these are not currently used in the ecosystem and would be stale pointers.
- Don't invent skill content in the umbrella — it should just list available skills (which starts as just itself).
- Don't hardcode a GitHub org other than `42euge` without asking.

## Completion

When this skill finishes, emit a trace:

```bash
"$CLAUDE_PLUGIN_ROOT/skills/self/skills/improve/resources/trace-emit.sh" \
  --skill geno-lifecycle-repo-create \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = repo scaffolded, git initialized, all files written
- `failure` = directory collision, git init failed, or file write failed
- `abandoned` = user stopped during naming or detail gathering
