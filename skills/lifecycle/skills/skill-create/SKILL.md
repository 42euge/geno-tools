---
name: geno-lifecycle-skill-create
description: >-
  Scaffold a new skill in a geno ecosystem repo. Creates the SKILL.md with
  proper frontmatter, updates the umbrella skill table and GENO.md skills
  table. Use when user says /geno-skills-create, wants to add a new skill
  to a geno-* repo, or scaffold a SKILL.md.
argument-hint: "[skill-name|freeform description]"
allowed-tools: "Bash(find *) Bash(ls *) Bash(grep *) Bash(git *) Read(*) Write(*) Edit(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-skills-create — Skill Scaffolder

Creates a new skill in a geno ecosystem repo. Handles naming, SKILL.md generation, and updating the umbrella skill and GENO.md so the new skill is wired into the repo.

## When to invoke

- The user wants to add a new skill (slash command) to a geno-* repo.
- The user says "create a skill", "add a slash command", "scaffold a SKILL.md".
- The user is building a new capability in an existing skillset.

## Input

`$ARGUMENTS` is either:
- A skill name (e.g. `geno-dev-worktrees-manage`) — skip naming, go straight to details
- Freeform text describing what the skill should do — use it to derive the name
- Empty — launch the interactive flow

## Workflow

### 1. Determine target repo

Check the current working directory for signs of a geno ecosystem repo:
- Look for `genotools.yaml` at the repo root (or workspace root)
- Look for a `skills/` directory
- Look for `GENO.md` or `SKILL.md` at root

If inside a workspace (has `.geno/.workspace/workspace.yaml`), check `repos:` to find the target repo.

If no geno repo is detected, use `AskUserQuestion` to ask which repo to target. Accept a path, a skillset name (resolved via `geno-tools ls`), or a GitHub URL.

Once identified, record:
- `$REPO_ROOT` — absolute path to the repo root
- `$SKILLSET` — the skillset name (e.g. `geno-dev`, `geno-media`)

### 2. Inventory existing skills

Read the repo's skill landscape:

```bash
ls "$REPO_ROOT/skills/"
```

For each existing skill directory, read its SKILL.md frontmatter to extract `name` and `description`. Build a table of existing skills for reference.

Also read `$REPO_ROOT/GENO.md` (if it exists) to find the skills table.

### 3. Determine skill type

If `$ARGUMENTS` contains a fully qualified skill name (matches `geno-*-*-*` or `geno-*-*`), parse it:
- Extract the sub-skillset (pluralized noun segment)
- Extract the action verb segment

If `$ARGUMENTS` is freeform or empty, use `AskUserQuestion`:

> What kind of skill are you adding?
>
> - **Sub-skill** — a new capability under an existing sub-skillset (e.g. `geno-dev-worktrees-prune`)
> - **New sub-skillset** — a new group of related capabilities (e.g. `geno-dev-pipelines-*`)
> - **Umbrella** — the root skill for a new skillset repo (rare — only when creating a new repo)

### 4. Name the skill

#### Sub-skill under existing sub-skillset

Show the existing sub-skillsets in the repo and let the user pick one, then ask for the action verb:

> Which sub-skillset does this belong to?
> - tasks (existing: start, complete)
> - worktrees (existing: manage)
> - ...

> What action does this skill perform? (use a verb: create, list, sync, prune, etc.)

#### New sub-skillset

Ask for the sub-skillset noun (must be plural) and the first action verb:

> Sub-skillset name? (pluralized noun: pipelines, templates, configs, etc.)

> First action in this sub-skillset? (verb: create, list, sync, etc.)

#### Umbrella

The name is just the skillset name (e.g. `geno-{name}`). This is only for new repos that don't have an umbrella skill yet.

Construct the full name: `{skillset}-{sub-skillset}-{skill}` (e.g. `geno-dev-worktrees-prune`).

Validate:
- Sub-skillset is a pluralized noun (warn if it looks like a verb or adjective)
- Skill is an action verb (warn if it looks like a noun)
- The name doesn't collide with an existing skill

### 5. Gather skill details

Use `AskUserQuestion` to collect:

> Describe what this skill does in 1-2 sentences.

From the description, draft:
- `description` — the frontmatter description (include trigger phrases: "Use when user says /geno-{name}-{sub}-{action}")
- `allowed-tools` — infer from the description what tools the skill will need. Default to `"Bash(*) Read(*) Write(*) Edit(*)"` and suggest narrowing later.

Ask the user to confirm or edit the drafted description.

Optionally ask:
- `argument-hint` — if the skill takes arguments, what's the format?

### 6. Scaffold the skill

#### 6a. Create the directory and SKILL.md

```bash
mkdir -p "$REPO_ROOT/skills/$SKILL_NAME"
```

Write `$REPO_ROOT/skills/$SKILL_NAME/SKILL.md`:

```markdown
---
name: {skill-name}
description: >-
  {description, including "Use when user says /geno-{name}-{sub}-{action}"}
{if argument-hint}argument-hint: "{argument-hint}"
{end}allowed-tools: "{allowed-tools}"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# {skill-name} — {Short Title}

{One paragraph describing what the skill does and when to use it.}

## When to invoke

- {Trigger condition 1}
- {Trigger condition 2}
- {Trigger condition 3}

## Input

`$ARGUMENTS` — {describe expected arguments, or "No arguments." if none}.

## Workflow

### 1. {First step}

{Description of what to do.}

### 2. {Second step}

{Description of what to do.}

## Don'ts

- {Anti-pattern to avoid}
```

Present the full SKILL.md to the user for review before writing. Use `AskUserQuestion`:

> Here's the scaffolded SKILL.md. Want me to write it as-is, or would you like to edit it first?
> - **Write it** (Recommended)
> - **Edit first** — I'll ask what to change

If the user wants edits, iterate until they approve.

#### 6b. For umbrella skills

If the skill type is umbrella, write it at `$REPO_ROOT/skills/$SKILLSET/SKILL.md` (not a sub-skill path). The content follows the umbrella pattern — a table of available sub-skills rather than a single workflow.

### 7. Update the umbrella skill

Read `$REPO_ROOT/skills/$SKILLSET/SKILL.md` (the umbrella skill). Find the table or list that inventories sub-skills. Add a row for the new skill.

If the umbrella doesn't have a skills table, add one:

```markdown
## Skills

| Skill | Description |
|-------|-------------|
| {new-skill-name} | {short description} |
```

If it already has a table, append the new row in alphabetical order by skill name.

### 8. Update GENO.md

If `$REPO_ROOT/GENO.md` exists:
- Find the skills table (look for a table with columns like "Skill", "Sub-skillset", "Slash command")
- Add a row for the new skill:
  ```
  | {skill-name} | {sub-skillset} | /geno-{name}-{sub}-{action} |
  ```
- Insert in alphabetical order within the sub-skillset group

If `GENO.md` doesn't exist, skip this step and note it in the report.

### 9. Update the umbrella SKILL.md description

Read the umbrella skill's `description` field in its frontmatter. If it lists trigger phrases (e.g. "Use when user says /geno-dev-tasks-start, /geno-dev-commits-rewrite"), add the new skill's trigger phrase to the list.

### 10. Report

Tell the user:

- Created `skills/{skill-name}/SKILL.md`
- Updated umbrella skill at `skills/{skillset}/SKILL.md`
- Updated `GENO.md` skills table (or "GENO.md not found — update manually")
- Reminder: after fleshing out the skill body, re-register with `geno-tools update {skillset}` or reinstall to pick up the new skill in agent sessions

## Don'ts

- Don't use aliased prefixes like `gt-` in any generated content — always use canonical `geno-` prefix.
- Don't create skills outside the `skills/` directory.
- Don't overwrite an existing skill without asking — if the directory already exists, warn and ask.
- Don't generate a `commands/` directory — that's the legacy format.
- Don't restate ecosystem-wide conventions in the generated SKILL.md body — the skill should describe *itself*, not how the ecosystem works.
- Don't scaffold a full workflow implementation — the body should be a skeleton for the user to fill in. Provide structure (headings, placeholders) but not invented behavior.
