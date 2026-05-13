---
title: geno-tools
description: Installer and meta-CLI for geno-* skillsets
---

# geno-tools

Installer and meta-CLI for geno-* skillsets

[:material-github: GitHub](https://github.com/42euge/geno-tools){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-alias](#geno-alias) | `/geno-alias` | Create, remove, and list custom slash-command aliases for geno ecosystem skills. |
| [geno-audit](#geno-audit) | `/geno-audit` | Audit a geno-ecosystem repo for compliance with skillset conventions. |
| [geno-data-workspaces-init](#geno-data-workspaces-init) | `/geno-data-workspaces-init` | Create data workspaces for personal/life skills (taxes, remodel, career, custom). Scaffolds a dir... |
| [geno-icons](#geno-icons) | `/geno-icons` | Generate pixel art icons for geno-ecosystem projects using SD 1.5 + pixel art LoRA. |
| [geno-onboarding](#geno-onboarding) | `/geno-onboarding` | Walks an operator through onboarding a new skillset into a geno-tools install, including enterpri... |
| [geno-skills-create](#geno-skills-create) | `/geno-skills-create` | Scaffold a new skill in a geno ecosystem repo. Creates the SKILL.md with proper frontmatter, upda... |
| [geno-skills-install](#geno-skills-install) | `/geno-skills-install` | Install skills from a local geno ecosystem repo checkout globally via npx skills add. Detects the... |
| [geno-skills-status](#geno-skills-status) | `/geno-skills-status` | Show the installation status of the geno ecosystem — version, commit, branch, and freshness of ea... |
| [geno-tools-open-docs](#geno-tools-open-docs) | `/geno-tools-open-docs` | Open the current repo's GitHub Pages documentation site in the default browser. |
| [geno-tools-update](#geno-tools-update) | `/geno-tools-update` | Update installed geno ecosystem skillsets to the latest main branch. |

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-tools — Skillset Manager
    
    Orchestrator for the geno-* ecosystem. Manages installation, removal, and updates of skillset repos.
    
    ```!
    which geno-tools >/dev/null 2>&1 || echo "geno-tools CLI not on PATH. The plugin's SessionStart hook (Claude Code) and OpenCode plugin loader run scripts/bootstrap.sh automatically. On Gemini CLI / Codex / Cursor, run 'bash \$PLUGIN_ROOT/scripts/bootstrap.sh' once (\$PLUGIN_ROOT is e.g. ~/.gemini/extensions/geno-tools)."
    ```
    
    ## Available Skillsets
    
    Install by full repo name (e.g. `geno-tools install geno-<name>`):
    
    | Repo | Description |
    |------|-------------|
    | geno-agents | Agent coordination, presence, and multi-agent networking |
    | geno-media | Audiobooks (Kokoro TTS), animated videos (Manim), podcasts |
    | geno-research | Wiki-based research notes, paper generation, repo docs |
    | geno-kaggle | Kaggle benchmarks, competition notebooks, discussion scraping |
    | geno-dev | Developer utilities, Colab uploads, commit rewriting |
    
    ## Infrastructure Skills
    
    | Skill | Description |
    |-------|-------------|
    | geno-alias | Create, remove, and list custom slash-command aliases |
    | geno-data-workspaces-init | Create data workspaces for personal/life skills (taxes, remodel, career) |
    | geno-skills-create | Scaffold a new skill in a geno ecosystem repo |
    | geno-skills-install | Install skills from a local repo checkout globally |
    | geno-skills-status | Show version, commit, and freshness of installed skillsets |
    
    ## Commands
    
    - `geno-tools ls` — list installed skillsets and their active variant
    - `geno-tools ls --available` — show all registered skillsets in the registry
    - `geno-tools install <repo|url|path>` — install a skillset (clone, venv, register with all agents)
    - `geno-tools remove <repo> [--keep-data]` — uninstall a skillset from all agents
    - `geno-tools update [repo]` — pull latest for one or all skillsets
    - `geno-tools doctor` — verify symlinks, worktrees, venvs
    
    ## Source Resolution
    
    The `<repo>` argument resolves in order:
    1. Registered repo name (e.g. `geno-<name>`) -> git URL. Bare slug (e.g. `<name>`) is also accepted for backwards compatibility.
    2. Local directory path
    3. Git URL (https:// or git@)

## geno-alias

**Slash command:** `/geno-alias`
  **Arguments:** `[add|remove|list] [source-skill] [alias-name]`

> Create, remove, and list custom slash-command aliases for geno ecosystem skills.

??? info "Overview (Level 3)"

    Create custom slash-command aliases for any installed geno ecosystem skill. Aliases are tracked in `~/.geno/.genorc` and registered with all agents via `npx skills`.
    
    ## Argument parsing
    
    Parse `$ARGUMENTS` into one of three operations:
    
    | Input | Operation |
    |-------|-----------|
    | `list` or empty | List all aliases |
    | `remove <alias>` | Remove an alias |
    | `add <source> <alias>` | Create an alias |
    | `<source> <alias>` (two args, first is not `add`/`remove`/`list`) | Create an alias (shorthand) |
    
    Strip leading `/` from both source and alias names.
    
    ## Add operation
    
    ### Step 1 — Validate source skill exists
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

    # geno-alias — Skill Aliasing
    
    Create custom slash-command aliases for any installed geno ecosystem skill. Aliases are tracked in `~/.geno/.genorc` and registered with all agents via `npx skills`.
    
    ## Argument parsing
    
    Parse `$ARGUMENTS` into one of three operations:
    
    | Input | Operation |
    |-------|-----------|
    | `list` or empty | List all aliases |
    | `remove <alias>` | Remove an alias |
    | `add <source> <alias>` | Create an alias |
    | `<source> <alias>` (two args, first is not `add`/`remove`/`list`) | Create an alias (shorthand) |
    
    Strip leading `/` from both source and alias names.
    
    ## Add operation
    
    ### Step 1 — Validate source skill exists
    
    ```bash
    SOURCE="<source>"
    if [ -f "$HOME/.agents/skills/$SOURCE/SKILL.md" ]; then
      SRC_PATH="$HOME/.agents/skills/$SOURCE/SKILL.md"
    elif [ -f "$HOME/.claude/skills/$SOURCE/SKILL.md" ]; then
      SRC_PATH="$HOME/.claude/skills/$SOURCE/SKILL.md"
    else
      echo "Source skill '$SOURCE' not found."
      echo "Available skills:"
      ls ~/.agents/skills/ 2>/dev/null; ls ~/.claude/skills/ 2>/dev/null
      exit 1
    fi
    ```
    
    ### Step 2 — Validate alias doesn't shadow a non-alias skill
    
    Check `~/.geno/.genorc` — if the alias name already exists there, it's a previously created alias and can be overwritten. If it exists in `~/.agents/skills/` or `~/.claude/skills/` but is NOT in `.genorc`, warn that creating this alias would shadow an existing skill and ask the user to confirm.
    
    ### Step 3 — Create the alias SKILL.md
    
    Read the source SKILL.md. Create a copy with the `name:` field **removed** from the frontmatter (so `npx skills` derives the name from the directory). All other frontmatter and body content are preserved unchanged.
    
    ```bash
    mkdir -p "$HOME/.geno/aliases/ALIAS_NAME"
    ```
    
    Use `python3` to strip the `name:` field:
    
    ```bash
    python3 -c "
    import re, sys
    content = open(sys.argv[1]).read()
    parts = content.split('---', 2)
    if len(parts) >= 3:
        fm = re.sub(r'^name:.*\n', '', parts[1], flags=re.MULTILINE)
        result = '---' + fm + '---' + parts[2]
    else:
        result = content
    open(sys.argv[2], 'w').write(result)
    " "$SRC_PATH" "$HOME/.geno/aliases/ALIAS_NAME/SKILL.md"
    ```
    
    ### Step 4 — Register with npx skills
    
    ```bash
    npx --yes skills add "$HOME/.geno/aliases/ALIAS_NAME" --agent "*" --global --yes
    ```
    
    ### Step 5 — Record in .genorc
    
    ```bash
    python3 -c "
    import sys
    from pathlib import Path
    
    rc = Path.home() / '.geno' / '.genorc'
    # Read existing content or start fresh
    lines = rc.read_text().splitlines() if rc.exists() else []
    
    # Ensure 'aliases:' header exists
    if not any(l.strip() == 'aliases:' for l in lines):
        lines.append('aliases:')
    
    # Remove any existing entry for this alias
    alias, source = sys.argv[1], sys.argv[2]
    lines = [l for l in lines if not l.strip().startswith(alias + ':')]
    
    # Find the aliases: line and insert after it
    idx = next(i for i, l in enumerate(lines) if l.strip() == 'aliases:')
    lines.insert(idx + 1, f'  {alias}: {source}')
    
    rc.write_text('\n'.join(lines) + '\n')
    " "ALIAS_NAME" "SOURCE"
    ```
    
    ### Step 6 — Report
    
    Tell the user the alias was created. Note that it will take effect in the **next session** (since Claude Code loads skills at session start).
    
    ## Remove operation
    
    ### Step 1 — Look up alias in .genorc
    
    ```bash
    python3 -c "
    import sys, re
    from pathlib import Path
    rc = Path.home() / '.geno' / '.genorc'
    if not rc.exists():
        print('No aliases configured.'); sys.exit(1)
    content = rc.read_text()
    alias = sys.argv[1]
    m = re.search(rf'^\s+{re.escape(alias)}:\s+(.+)$', content, re.MULTILINE)
    if not m:
        print(f\"'{alias}' is not a registered alias.\"); sys.exit(1)
    print(m.group(1).strip())
    " "ALIAS_NAME"
    ```
    
    If not found, report that the alias doesn't exist and show available aliases.
    
    ### Step 2 — Unregister
    
    ```bash
    npx --yes skills remove "ALIAS_NAME" --agent "*" --global --yes
    ```
    
    ### Step 3 — Clean up files
    
    ```bash
    rm -rf "$HOME/.geno/aliases/ALIAS_NAME"
    ```
    
    ### Step 4 — Remove from .genorc
    
    ```bash
    python3 -c "
    import re, sys
    from pathlib import Path
    rc = Path.home() / '.geno' / '.genorc'
    content = rc.read_text()
    alias = sys.argv[1]
    content = re.sub(rf'^\s+{re.escape(alias)}:.*\n', '', content, flags=re.MULTILINE)
    # Remove 'aliases:' header if no entries remain
    if re.search(r'^aliases:\s*$', content, re.MULTILINE) and not re.search(r'^  \w', content, re.MULTILINE):
        content = re.sub(r'^aliases:\s*\n', '', content, flags=re.MULTILINE)
    content = content.strip()
    if content:
        rc.write_text(content + '\n')
    else:
        rc.unlink()
    " "ALIAS_NAME"
    ```
    
    ### Step 5 — Report
    
    Tell the user the alias was removed and will disappear next session.
    
    ## List operation
    
    ```bash
    python3 -c "
    from pathlib import Path
    import re
    rc = Path.home() / '.geno' / '.genorc'
    if not rc.exists():
        print('No aliases configured.'); raise SystemExit
    content = rc.read_text()
    entries = re.findall(r'^\s+(\S+):\s+(\S+)', content, re.MULTILINE)
    if not entries:
        print('No aliases configured.'); raise SystemExit
    print(f'{len(entries)} alias(es):\n')
    for alias, source in sorted(entries):
        installed = 'installed' if (Path.home() / '.claude/skills' / alias).exists() else 'not installed'
        print(f'  /{alias}  ->  /{source}  ({installed})')
    "
    ```
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-alias \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = alias created, removed, or listed without errors
    - `failure` = source skill not found, npx registration failed, or .genorc write error
    - `abandoned` = user stopped early

## geno-audit

**Slash command:** `/geno-audit`

> Audit a geno-ecosystem repo for compliance with skillset conventions.

??? info "Overview (Level 3)"

    Validates that a `geno-{name}` repo meets the conventions required for installation and management by `geno-tools`.
    
    The audit runs checks in three tiers: **required** (FAIL), **recommended** (WARN), and **optional** (INFO). A repo must pass all required checks to be installable via `geno-tools install`.
    
    ---
    
    ## `.geno` Directory Convention
    
    Every project in the geno ecosystem uses a two-tier `.geno` directory structure for runtime state, configuration, and tooling data. Neither tier should ever be committed to git — they contain machine-local paths, user-specific config, and transient runtime state that would break on any other machine.
    
    ### Global — `~/.geno/`
    
    The global `.geno` directory at `~/.geno/` is the ecosystem-wide root. It contains shared infrastructure and per-project state that persists across workspaces:
    
    ```
    ~/.geno/
    ├── config.yaml                    # ecosystem-wide settings
    ├── agents/                        # agent registration and presence
    ├── sessions/                      # session history
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

    # geno-audit — Ecosystem Compliance Auditor
    
    Validates that a `geno-{name}` repo meets the conventions required for installation and management by `geno-tools`.
    
    The audit runs checks in three tiers: **required** (FAIL), **recommended** (WARN), and **optional** (INFO). A repo must pass all required checks to be installable via `geno-tools install`.
    
    ---
    
    ## `.geno` Directory Convention
    
    Every project in the geno ecosystem uses a two-tier `.geno` directory structure for runtime state, configuration, and tooling data. Neither tier should ever be committed to git — they contain machine-local paths, user-specific config, and transient runtime state that would break on any other machine.
    
    ### Global — `~/.geno/`
    
    The global `.geno` directory at `~/.geno/` is the ecosystem-wide root. It contains shared infrastructure and per-project state that persists across workspaces:
    
    ```
    ~/.geno/
    ├── config.yaml                    # ecosystem-wide settings
    ├── agents/                        # agent registration and presence
    ├── sessions/                      # session history
    ├── messages/                      # inter-agent messages
    ├── bin/                           # symlinked CLI binaries
    ├── venv/                          # shared Python environments
    └── geno-{name}/                   # per-skillset state
        ├── .git/                      # bare repo
        ├── main/                      # primary worktree
        ├── .worktrees/<variant>/      # additional worktrees
        ├── venvs/<venv-name>/         # isolated Python envs
        └── active -> main             # symlink to active variant
    ```
    
    This is where `geno-tools install` clones repos, creates venvs, and materializes bin symlinks. Other ecosystem tools also keep state here — `geno-notes` stores the global task journal at `~/.geno/geno-notes/`, `geno-agents` stores registration data at `~/.geno/agents/`, etc.
    
    ### Local — `.geno/`
    
    The local `.geno/` directory at the repo or workspace root holds per-workspace state. It has a fixed structure with a reserved `.workspace/` subdirectory for workspace metadata, and optional `{project-name}/` subdirectories for tools that need local state.
    
    ```
    .geno/
    ├── .workspace/                    # workspace metadata (managed by geno-dev-workspaces-init)
    │   ├── workspace.yaml             # slug, status, repos, color, ticket
    │   └── worktrees/                 # local worktree checkouts
    │       └── {repo}/{branch}/       # one per active worktree
    └── {project-name}/                # per-tool local state (optional)
        └── ...                        # tool-specific files
    ```
    
    **`.workspace/`** contains workspace metadata — the `workspace.yaml` (slug, status, repos, color assignment, source ticket) and any worktree checkouts created for repos in this workspace. This is always under `.workspace/` to keep it separate from tool state.
    
    **`{project-name}/`** directories are created by individual tools when they need workspace-scoped state. For example, `geno-notes` may create `.geno/geno-notes/` to store project-scoped tasks and journal entries (as opposed to the global journal at `~/.geno/geno-notes/`). Not every workspace will have these — they appear only when a tool that needs local state is used in that workspace.
    
    ### Audit checks
    
    **Required:**
    - `.geno/` is not tracked by git (checked via `git ls-files`)
    - `CLAUDE.local.md` is not tracked by git
    
    **Recommended:**
    - Global gitignore (`~/.config/git/ignore`) includes `.geno/` and `CLAUDE.local.md`. These entries belong in the global gitignore, not in any project's `.gitignore` — adding them to a project's `.gitignore` would leak geno ecosystem artifacts into committed files. The audit should check the global gitignore and suggest adding entries there if missing. Never modify a project's `.gitignore` for geno-specific patterns.
    
    ---
    
    ## Manifest — `genotools.yaml`
    
    `genotools.yaml` is the manifest file every geno-* skillset must have at its root. It's what `geno-tools install` reads to know how to set up the skillset: what it's called, what version it is, whether it needs a Python venv, what scripts to symlink into `~/.geno/{project-name}/`, and what config files to copy on first install. Without a valid manifest, `geno-tools` doesn't know what it's installing and the install will fail.
    
    **Required:**
    - File exists at repo root
    - Has a `name` field (the skillset name — `geno-` prefix is stripped if present)
    - Has a `version` field (semver string, e.g. `0.1.0`)
    - Has a non-empty `description` field
    
    **Recommended:**
    - `name` matches the repo directory name (with or without the `geno-` prefix)
    
    **Optional:**
    - If `venv` section exists, it should have `name` and `deps` fields
    - If `runtime` section exists, each entry should have `src` and `dst`
    - If `config` section exists, each entry should have `src` and `dst`
    - If `pyproject.toml` also exists, its `project.name` should match the manifest name
    
    ---
    
    ## Versioning
    
    The `version` field in `genotools.yaml` is the canonical version for every skillset. When a repo also has `pyproject.toml`, `package.json`, or a Python `__init__.py` with version fields, they must all agree. The audit checks consistency and detects unreleased work that may warrant a bump.
    
    ### Audit checks
    
    **Required:**
    - `genotools.yaml` `version` is a valid semver string (MAJOR.MINOR.PATCH)
    
    **Recommended:**
    - If `pyproject.toml` exists and has `project.version`, it matches `genotools.yaml` version
    - If `package.json` exists and has `version`, it matches `genotools.yaml` version
    - If root `SKILL.md` has `metadata.version` in frontmatter, it matches `genotools.yaml` version
    - If a Python `__init__.py` in the package root has `__version__`, it matches `genotools.yaml` version
    
    **Info:**
    - If skills have been added or removed since the last git tag (compare `skills/` directories against the most recent tag), note that a version bump may be warranted
    
    ---
    
    ## Umbrella Skill — `SKILL.md`
    
    `SKILL.md` at the repo root is the umbrella manifest that describes the skillset to Claude Code and other agents. When `geno-tools install` runs `npx skills add`, this file is what gets registered — it tells the agent what the skillset does, when to use it, and what tools it's allowed to call. A skillset without a valid `SKILL.md` will install on disk but won't be usable by any agent.
    
    **Required:**
    - File exists at repo root
    - Has YAML frontmatter delimited by `---`
    - Frontmatter includes a `name` field
    - Frontmatter includes a non-empty `description` field
    
    **Recommended:**
    - `name` in frontmatter matches the repo name
    - Frontmatter includes `allowed-tools` declaring what tools the skill needs
    
    **Optional:**
    - Frontmatter includes `metadata` with `author` and `version`
    
    ---
    
    ## Skill Nomenclature
    
    Skills follow a three-level naming hierarchy: **skillset → sub-skillset → skill**. The full spec lives at `docs/skillsets/nomenclature.md` (published at `https://42euge.github.io/geno-tools/skillsets/nomenclature/`). The audit enforces it.
    
    Quick reference: `{skillset}-{sub-skillset}-{skill}` where sub-skillset is a **pluralized noun** and skill is an **action verb**. The umbrella skill is just the skillset name. Directory names under `skills/` must match the `name` field in each SKILL.md frontmatter.
    
    ### Legacy `commands/` directory
    
    Some repos still have a `commands/` directory with `gt-*.md` files from the old slash-command convention. This is legacy — all skill definitions now live under `skills/` as `SKILL.md` files. If a repo has both `commands/` and `skills/`, the `commands/` directory must be removed. Do not keep it for backward compatibility — `geno-tools install` registers skills from `skills/`, not `commands/`.
    
    If `commands/` contains content that hasn't been migrated to `skills/` yet, migrate it: create the appropriate `skills/{skillset}-{sub-skillset}-{skill}/SKILL.md` file with proper frontmatter, move the command body into it, then delete the command file. Do not leave both in place.
    
    ### Audit checks
    
    **Required:**
    - An umbrella skill exists at `skills/{skillset}/SKILL.md`
    - Every directory under `skills/` contains a `SKILL.md`
    - No `commands/` directory exists — if found, migrate contents to `skills/` and delete it
    - **Monolithic CLI check**: if the skillset has a CLI backend (`[project.scripts]` in `pyproject.toml` or a standalone bin script) with multiple subcommands, it must have corresponding sub-skillset skill directories under `skills/` beyond the umbrella. To check: (a) find the CLI entry point from `[project.scripts]` and inspect it for `add_parser` / `add_command` / `app.command` / `@cli.command` calls (argparse, click, typer) to count subcommands; (b) count directories under `skills/` that contain a `SKILL.md` and subtract 1 for the umbrella. A skillset with ≥ 3 CLI subcommands and 0 sub-skillset skill directories **fails**. A comment in `CLAUDE.md` or `GENO.md` claiming the repo is a "single-skill skillset" does not exempt it from this check. **Correct pattern**: geno-dev (`geno-dev-tasks-start`, `geno-dev-commits-rewrite`, `geno-dev-loops-cruise`, `geno-dev-sessions-fork`, etc. — 9 sub-skills for 9 functional groups). **Failure example**: geno-notes (18 CLI subcommands — add, start, done, abandon, note, inbox, triage, list, show, search, promote, reindex, compile, lint, site, path, scope, init — but only the umbrella skill under `skills/`).
    
    **Recommended:**
    - All skill directory names follow the `{skillset}-{sub-skillset}-{skill}` pattern
    - Sub-skillset segment is a pluralized noun (not a verb or adjective)
    - Skill segment is an action verb
    - The `name` field in each SKILL.md frontmatter matches its directory name
    - The umbrella skill's `description` lists all available sub-skill commands
    - No skill directories exist outside of `skills/`
    
    ---
    
    ## Agent Instruction Files
    
    Coding agents read repo-level instruction files to understand architecture, entry points, and conventions. Without these, agents rediscover the repo structure every session. Each agent has its own file convention:
    
    | Agent | Instruction file | Notes |
    |-------|-----------------|-------|
    | Claude Code | `CLAUDE.md` | Read automatically on session start |
    | Gemini CLI | `GEMINI.md` | Pointed to by `gemini-extension.json` via `contextFileName` |
    | OpenAI Codex | `AGENTS.md` | Read automatically on session start |
    | OpenCode | `.opencode/INSTALL.md` | Plugin-based — context loaded via `.opencode/plugins/` |
    
    ### Single source of truth — `GENO.md`
    
    Rather than maintaining duplicate content across `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, and OpenCode configs, every geno-* repo should have a single `GENO.md` file at the repo root containing all agent instructions. The per-agent files become thin pointers that import it:
    
    ### What goes in `GENO.md`
    
    `GENO.md` is the canonical instruction file — the single document any agent reads to understand the repo cold. It should contain everything an agent needs to start working without asking questions or exploring the codebase first. Write it for an agent that just walked into the room: no prior context, no assumptions.
    
    #### Required sections
    
    1. **Title and summary** — one-line description of what this skillset does, framed agent-neutrally.
    
    2. **Skills table** — every skill in the repo with its name, sub-skillset group, and slash command. This is the index an agent checks to understand what capabilities are available.
    
       ```markdown
       | Skill | Sub-skillset | Slash command |
       |-------|-------------|---------------|
       | geno-{name} | — | — (umbrella) |
       | geno-{name}-tasks-start | tasks | /geno-{name}-tasks-start |
       ```
    
    3. **Repo structure** — a tree showing the key files and directories. Agents use this to navigate without running `find`. Include what each directory/file is for.
    
       ```markdown
       ## Repo structure
    
       geno-{name}/
       ├── GENO.md              # agent instructions (this file)
       ├── SKILL.md             # umbrella skill manifest
       ├── genotools.yaml       # geno-tools manifest
       ├── skills/              # skill definitions
       │   ├── geno-{name}/     #   umbrella
       │   └── geno-{name}-*/   #   sub-skills
       ├── docs/                # MkDocs Material site
       └── pyproject.toml       # Python package (if applicable)
       ```
    
    4. **Conventions** — the rules an agent must follow when modifying code in this repo. This is where naming conventions, file placement rules, and contribution workflows live. Key conventions to document:
    
       - **Nomenclature**: how skills are named in this repo (e.g. `geno-{name}-{sub-skillset}-{skill}`). Do not restate ecosystem-wide naming rules — just show the pattern as it applies to this skillset.
       - **SKILL.md frontmatter**: required fields and format for new skills
       - **Adding a new skill**: step-by-step checklist (create directory under `skills/`, write SKILL.md with frontmatter, update umbrella description, update docs, update this file's skills table)
       - **Command prefix aliasing**: slash commands in repo source files must always use the canonical `geno-` prefix (e.g. `/geno-{name}-tasks-start`). The prefix users type (`/gt-`, `/geno-`, or bare `/`) is configured per-installation in `~/.geno/config.yaml` and applied at install time by `geno-tools install`. Never hardcode an aliased prefix like `gt-` in SKILL.md descriptions, GENO.md, or any committed file.
       - **Versioning**: which files contain the version number (always `genotools.yaml`; plus any others like `pyproject.toml` or `package.json`) and the rule that the version must be bumped when adding/removing skills or changing behavior
    
    #### Recommended sections
    
    5. **Architecture / how it works** — for skillsets with runtime code (Python packages, scripts), explain the entry points, key modules, and data flow. Skip this for pure-markdown skillsets.
    
    6. **Dependencies and runtime** — if the skillset needs a venv, external tools, or system dependencies, list them here so agents know what's available and what constraints exist.
    
    #### What NOT to put in `GENO.md`
    
    - Install instructions for end users — those go in `README.md` and `docs/getting-started.md`
    - Agent-specific syntax or references — this file is read by all agents
    - Transient state like current tasks or in-progress work — those go in `.geno/` or conversation context
    
    ### Per-agent pointer files
    
    The per-agent files are thin pointers. No content lives in them — they exist only because each agent looks for a different filename.
    
    **`CLAUDE.md`**:
    ```markdown
    @./GENO.md
    ```
    
    **`GEMINI.md`**:
    ```markdown
    @./GENO.md
    ```
    
    **`AGENTS.md`**:
    ```markdown
    @import GENO.md
    ```
    
    **`gemini-extension.json`** (if present):
    ```json
    {
      "name": "geno-{name}",
      "description": "...",
      "version": "0.1.0",
      "contextFileName": "GEMINI.md"
    }
    ```
    
    This way, updating `GENO.md` updates every agent at once. No content lives in the per-agent files — they are pure pointers.
    
    ### Audit checks
    
    **Required:**
    - `GENO.md` exists at repo root and is non-empty
    
    **Recommended:**
    - `CLAUDE.md` exists and contains only `@./GENO.md` (no other content)
    - `GEMINI.md` exists and contains only `@./GENO.md`
    - `AGENTS.md` exists and contains only `@import GENO.md`
    - If `gemini-extension.json` exists, its `contextFileName` points to `GEMINI.md`
    - No agent instruction content is duplicated across files — all substance lives in `GENO.md`
    - `GENO.md` contains a Conventions section (a heading matching `Conventions`, case-insensitive)
    - `GENO.md` Conventions section mentions command prefix aliasing — at minimum, states that source files use canonical `geno-` prefixed names for slash commands, not aliased prefixes
    - `GENO.md` Conventions section includes skill creation guidance — at minimum, a checklist for adding a new skill
    - `GENO.md` skills table uses canonical `/geno-{name}-*` slash command names, not aliased forms like `/gt-*`
    - `GENO.md` Conventions section includes versioning guidance — at minimum, identifies which files contain the version and states that the version should be bumped when skills are added, removed, or behavior changes
    
    ---
    
    ## Documentation — `docs/`
    
    Every geno-* repo should ship a MkDocs Material documentation site. This is how users and contributors learn what the skillset does, how to use it, and how it's built. The convention follows geno-tools' own docs structure, minus the animated landing page (that's unique to geno-tools as the ecosystem entry point).
    
    ### Required structure
    
    ```
    docs/
    ├── index.md                       # docs home — title, one-paragraph summary, nav links
    ├── getting-started.md             # install, prerequisites, first use
    └── assets/
        └── icon.png                   # project icon (generated via geno-icons)
    ```
    
    ### Recommended additions
    
    ```
    docs/
    ├── cli-reference.md               # if the skillset has CLI commands
    ├── architecture/
    │   └── index.md                   # how it works internally
    ├── stylesheets/
    │   └── extra.css                  # custom styles (dark/light theme support)
    └── <topic>/                       # domain-specific sections as needed
        └── index.md
    ```
    
    ### `mkdocs.yml`
    
    Each repo needs a `mkdocs.yml` at the repo root. Follow geno-tools' theme configuration (Material, Inter/JetBrains Mono fonts, light/dark toggle, navigation features) but skip:
    - `custom_dir: docs/overrides` (no hero overrides)
    - `extra_javascript` for `face.js` (no animated splash)
    - The `docs-home.md` hero page with feature cards
    
    A minimal `mkdocs.yml`:
    
    ```yaml
    site_name: geno-{name}
    site_description: One-line description
    site_url: https://42euge.github.io/geno-{name}
    repo_url: https://github.com/42euge/geno-{name}
    repo_name: 42euge/geno-{name}
    
    theme:
      name: material
      palette:
        - media: "(prefers-color-scheme: light)"
          scheme: default
          primary: custom
          accent: custom
          toggle:
            icon: material/brightness-7
            name: Switch to dark mode
        - media: "(prefers-color-scheme: dark)"
          scheme: slate
          primary: custom
          accent: custom
          toggle:
            icon: material/brightness-4
            name: Switch to light mode
      font:
        text: Inter
        code: JetBrains Mono
      icon:
        repo: fontawesome/brands/github
      features:
        - navigation.sections
        - navigation.top
        - content.code.copy
        - search.highlight
        - toc.follow
    
    nav:
      - Home: index.md
      - Getting Started: getting-started.md
      # ... additional pages
    
    markdown_extensions:
      - admonition
      - pymdownx.details
      - pymdownx.superfences
      - pymdownx.highlight:
          anchor_linenums: true
      - pymdownx.inlinehilite
      - pymdownx.tabbed:
          alternate_style: true
      - attr_list
      - toc:
          permalink: true
    ```
    
    ### Audit checks
    
    **Recommended:**
    - `docs/` directory exists
    - `docs/index.md` exists
    - `docs/getting-started.md` exists
    - `mkdocs.yml` exists at repo root
    - `mkdocs.yml` uses `material` theme
    
    **Optional:**
    - `docs/assets/icon.png` exists
    - `docs/cli-reference.md` exists (if the skillset exposes CLI commands)
    - `mkdocs.yml` has `site_url` and `repo_url` configured
    
    ---
    
    ## Repo Hygiene
    
    General repo quality checks. None block installation, but they prevent common issues.
    
    **Recommended:**
    - `README.md` exists — human-readable documentation for anyone browsing the repo on GitHub.
    - `LICENSE` file exists — declares the license so others know if they can use the skillset.
    - Repo directory name matches `geno-*` convention.
    
    ---
    
    ## Agent-Agnostic Language
    
    The geno ecosystem is CLI-agnostic — skillsets work with Claude Code, Gemini CLI, Codex, OpenCode, and any future coding agent. Documentation and user-facing text must reflect this. Referring to "Claude Code" as if it's the only supported agent misleads users and creates the impression that the skillset is locked to one platform.
    
    Use generic terms like "coding agent", "agent session", or "coding CLI" instead of naming a specific agent. When listing prerequisites, mention the supported agents rather than singling one out. When describing how to invoke a skill, show the generic form.
    
    **Avoid:**
    - "Developer skills for Claude Code"
    - "Prerequisites: Claude Code installed"
    - "From within a Claude Code session"
    - "Claude Code slash commands"
    
    **Prefer:**
    - "Developer skills for AI coding agents"
    - "Prerequisites: a supported coding CLI (Claude Code, Gemini CLI, Codex, or OpenCode)"
    - "From within an agent session"
    - "Slash commands" (no agent prefix)
    
    **Do NOT replace** references to agent-specific features, paths, or APIs that are genuinely specific to one agent. For example:
    - `.claude/worktrees/` — this is a real Claude Code directory path, not branding
    - "Codex sandbox" — this is a Codex-specific runtime concept
    - "Gemini CLI extension" — this refers to the actual Gemini extension format
    - Agent-specific plugin manifests (`.claude-plugin/`, `.codex-plugin/`, etc.)
    
    The rule is about how the *skillset itself* is described, not about suppressing legitimate references to agent-specific behavior within skill instructions.
    
    ### Audit checks
    
    **Recommended:**
    - Scan `README.md`, `docs/**/*.md`, `SKILL.md`, `AGENTS.md`, `GEMINI.md`, and `getting-started.md` for language that frames the skillset as exclusive to one agent
    - Descriptions and headings should use agent-neutral phrasing
    - Prerequisites should list supported CLIs generically, not single out one
    - Do not modify references to agent-specific features, paths, directories, or APIs — only replace branding/framing language
    
    ---
    
    ## Installation Compliance
    
    Geno-* skillsets must be installed through `geno-tools`, not by calling `npx skills add` directly. `geno-tools install` does more than just register skills — it clones the repo, creates venvs, materializes bin symlinks, and sets up the `~/.geno/geno-{name}/` directory structure. Bypassing it with `npx skills add` skips all of that, leaving the skillset partially installed: skills appear in the agent but the underlying tooling, venvs, and state directories are missing.
    
    Docs, READMEs, and getting-started guides should instruct users to install via `geno-tools`:
    
    ```bash
    geno-tools install geno-dev
    ```
    
    or via the skill within an agent session:
    
    ```
    /geno-tools install geno-dev
    ```
    
    Never instruct users to run `npx skills add <user>/<repo>` directly. That's an internal implementation detail of how `geno-tools install` registers skills — it should not be user-facing.
    
    Docs should always use the canonical `geno-tools install geno-{name}` or `/geno-tools install geno-{name}` form. Command aliases are user-configured and vary per installation, so they must never appear in repo documentation.
    
    This rule applies to install commands. For the general rule about slash command prefixes across all repo content, see **Command Prefix Aliasing in Repo Source** below.
    
    ### Audit checks
    
    **Recommended:**
    - No file in the repo contains `npx skills add` as a user-facing install instruction. Check `README.md`, `docs/**/*.md`, `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `SKILL.md` for this pattern.
    - Install instructions use the canonical `geno-tools install geno-{name}` or `/geno-tools install geno-{name}` form, not raw `npx`, `pip install`, or any aliased command names.
    
    ---
    
    ## Ecosystem Freshness
    
    Installed skillsets should stay on the latest main branch. Stale installs lead to agents using outdated skill definitions, missing features, and broken cross-skillset interactions. `geno-tools update` pulls the latest main for all installed skillsets (or a specific one) and re-registers skills.
    
    ### Audit checks
    
    **Recommended:**
    - Run `geno-tools update` as part of the audit to ensure the target repo's installed copy (if any) is on the latest main. If the installed copy is behind origin, the audit should note how many commits behind it is.
    - If the target repo's `main` worktree at `~/.geno-tools/geno-{name}/main/` has a dirty working tree or is on a non-default branch, warn that the install is in a non-standard state.
    
    **Info:**
    - Report the current installed revision (short SHA) and the date of the last commit on main. Stale installs older than 30 days get an INFO note.
    
    ---
    
    ## Command Prefix Aliasing in Repo Source
    
    Slash commands in the geno ecosystem use a configurable prefix. Users set their preferred prefix in `~/.geno/config.yaml`:
    
    ```yaml
    aliases:
      command_prefix: "gt"   # /gt-install, /gt-media-audiobook-create
      # or "geno"            # /geno-install, /geno-media-audiobook-create
      # or ""                # /install, /media-audiobook-create
    ```
    
    The prefix is applied at install time by `geno-tools install` when materializing skills via `npx skills add`. Repo source files — SKILL.md frontmatter, SKILL.md body, GENO.md, README.md, docs — must always use the **canonical name**, which uses the `geno-` prefix. The canonical name is the skill's `name` field in its SKILL.md frontmatter (e.g. `geno-notes`, `geno-dev-tasks-start`).
    
    ### What to check
    
    Scan all committed files that reference slash commands: SKILL.md (root and `skills/*/SKILL.md`), GENO.md, README.md, `docs/**/*.md`, CLAUDE.md, AGENTS.md, GEMINI.md.
    
    Look for patterns that indicate an aliased prefix was hardcoded:
    
    - `/gt-` followed by a skill name (e.g. `/gt-notes`, `/gt-dev-tasks-start`, `/gt-research`)
    - `gt-` used as a command prefix in section headers (e.g. `### /gt-notes add`)
    - Any non-`geno-` prefix in slash command references
    
    Do NOT flag:
    
    - The string `gt-` in contexts that aren't slash command references (e.g. `gt-*.md` when referring to legacy file naming, or `"gt"` as a config value example)
    - References to `command_prefix: "gt"` in configuration examples — those describe the user config, not a hardcoded command name
    - The `name` field in SKILL.md frontmatter — this should already be canonical (`geno-*`), but if it's wrong, that's caught by the Skill Nomenclature checks
    
    ### How to fix
    
    Replace every aliased slash command reference with its canonical form:
    
    - `/gt-notes` → `/geno-notes`
    - `/gt-dev-tasks-start` → `/geno-dev-tasks-start`
    - `/gt-research-paper-generate` → `/geno-research-paper-generate`
    
    In SKILL.md `description` fields, replace trigger phrases like `Use when user says /gt-foo` with `Use when user says /geno-foo`.
    
    ### Audit checks
    
    **Required:**
    - No SKILL.md file (root or under `skills/`) contains aliased command prefixes like `/gt-` in its `description` frontmatter field or body content. Slash command references must use the canonical `geno-` prefix. This is a functional requirement — agents use these descriptions to match user intent to skills, and aliased names may not match the installed command name.
    
    **Recommended:**
    - No file in the repo (`GENO.md`, `README.md`, `docs/**/*.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) contains aliased slash command references. All slash command references use the canonical `geno-` prefix.
    
    ---
    
    ## Single Source of Truth Enforcement
    
    **geno-tools is the single source of truth for the geno ecosystem.** This means every ecosystem-wide convention — how skills are named, what files a repo must have, how SKILL.md frontmatter is formatted, how to add a new skill — is defined exactly once, in the geno-tools repo (its docs, this audit spec, and its own codebase). No other repo defines, restates, or interprets these rules.
    
    Individual repos describe *themselves* — what skills they contain, what they do, how their specific code is structured. They do not describe *how the ecosystem works*. That boundary is what "single source of truth" means: geno-tools owns the rules, other repos follow them.
    
    When a repo restates a convention from geno-tools, it creates a copy. Copies drift. An agent reading geno-dev's local nomenclature section might get rules that were correct six months ago but have since been updated in geno-tools. Now two sources disagree and neither knows it. The audit prevents this by detecting and removing locally redefined conventions.
    
    ### What counts as a local redefinition
    
    Sections in repo files that restate ecosystem-level rules. These include but are not limited to:
    
    - Nomenclature rules (how skills/sub-skillsets/slugs are named)
    - Required repo structure definitions (what files every geno-* repo must have)
    - SKILL.md frontmatter format specifications
    - Step-by-step checklists for adding a new skill
    - Ecosystem-level compliance rules
    
    ### What to scan
    
    Check all markdown files that agents or contributors read: `GENO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md`, and `docs/**/*.md`.
    
    ### How to detect
    
    Look for sections that match these patterns:
    
    - Headings containing: `Nomenclature`, `Compliance`, `Convention`, `Repo structure`, `Required files`, `Frontmatter format`, `Adding a new skill`, `Contribution guide` (when it restates ecosystem rules rather than repo-specific workflows)
    - Paragraphs that define what "every geno-* repo must have" or "every SKILL.md must include"
    - Tables or lists that redefine the `{skillset}-{sub-skillset}-{skill}` naming pattern
    - References to the geno-tools nomenclature spec followed by a local restatement of the same rules
    
    ### What to do
    
    Remove the offending sections entirely. If the file becomes empty or loses important repo-specific content in the process, preserve only the repo-specific parts. If a section mixes ecosystem rules with repo-specific details (e.g. a compliance section that restates nomenclature rules but also lists this repo's specific skills), keep only the repo-specific content.
    
    A repo's `GENO.md` should contain a skills table showing what skills *this* repo has — that's repo-specific. It should not explain *how to name* skills in general — that's the ecosystem spec.
    
    ### Audit checks
    
    **Required:**
    - No file in the repo contains locally redefined ecosystem conventions. If found, remove them and note the removal in the PR.
    
    ---
    
    ## Running the Audit
    
    ### Input
    
    `$ARGUMENTS` — the target repo. Accepts:
    - A skillset short name (e.g. `dev`, `media`, `research`) — resolved via the registry
    - A GitHub URL
    - A local path to a repo directory
    - Empty — audits the current working directory
    
    ### Procedure
    
    1. **Clone the target into a fresh working copy.** Never operate on an existing workspace checkout — always clone into an isolated directory so the audit doesn't interfere with other agents or in-progress work.
    
       - If `$ARGUMENTS` is a short name, resolve it to a GitHub URL via the registry (`genotools/registry.py` or `geno-tools ls --available`)
       - If `$ARGUMENTS` is a GitHub URL, use it directly
       - If `$ARGUMENTS` is a local path or empty, skip cloning and work in-place
    
       Clone to a temporary directory within the current workspace:
       ```bash
       AUDIT_DIR="$(pwd)/.geno-audit/geno-{name}"
       git clone <url> "$AUDIT_DIR"
       cd "$AUDIT_DIR"
       ```
    
    2. **Detect the repo name.** Use the directory basename.
    
    3. **Run all checks.** For each section (`.geno` Convention, Manifest, SKILL.md, Skill Nomenclature, Agent Instruction Files, Documentation, Repo Hygiene, Agent-Agnostic Language, Installation Compliance, Ecosystem Freshness, Command Prefix Aliasing in Repo Source, Single Source of Truth Enforcement), check every item at every tier. For each check, determine PASS, FAIL, WARN, or INFO and collect a short reason for non-PASS results.
    
    4. **Parse YAML carefully.** Use Python for YAML parsing:
       ```bash
       python3 -c "
       import yaml, sys, json
       with open(sys.argv[1]) as f:
           data = yaml.safe_load(f)
       print(json.dumps(data, default=str))
       " <file>
       ```
       For SKILL.md frontmatter, extract the YAML between the first pair of `---` lines:
       ```bash
       python3 -c "
       import yaml, sys, json
       text = open(sys.argv[1]).read()
       if text.startswith('---'):
           end = text.index('---', 3)
           fm = yaml.safe_load(text[3:end])
           print(json.dumps(fm, default=str))
       else:
           print('null')
       " <file>
       ```
    
    5. **Fix all non-PASS items.** After running the checks, fix every FAIL, WARN, and INFO item that can be addressed:
       - Create missing files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, `LICENSE`, `docs/`, `mkdocs.yml`, etc.) using the conventions defined in this document
       - Add missing fields to `genotools.yaml` or `SKILL.md` frontmatter
       - For `CLAUDE.md` / agent instruction files, generate content from the repo's `SKILL.md`, `genotools.yaml`, and code structure
       - For `docs/`, scaffold the required structure (`index.md`, `getting-started.md`) and `mkdocs.yml` using the template from the Documentation section
       - For `README.md`, generate from the manifest description and SKILL.md
       - Do not modify the project's `.gitignore` for `.geno/` or `CLAUDE.local.md` — those belong in the global gitignore only
    
    6. **Create a PR with the fixes.** Once all fixable items are addressed:
       - Create a branch named `chore/geno-audit-compliance`
       - Commit all changes with a message summarizing what was added/fixed
       - Push and open a PR with the audit report as the body
    
       PR format:
       ```
       gh pr create --title "chore(geno-audit): bring repo into ecosystem compliance" --body "$(cat <<'EOF'
       ## Audit Report: geno-{name}
    
       Automated compliance audit via `geno-audit`.
    
       ### Summary
         PASS: NN    FAIL: NN fixed    WARN: NN fixed    INFO: NN fixed
    
       ### Changes
    
       - [list of files created or modified, grouped by audit section]
    
       ### Remaining items (if any)
    
       - [items that could not be auto-fixed, with explanation]
       EOF
       )"
       ```
    
    7. **Clean up.** Remove the cloned directory after the PR is created:
       ```bash
       rm -rf "$AUDIT_DIR"
       ```
       If the entire `.geno-audit/` directory is now empty, remove it too.
    
    8. **Report the result.** Print the PR URL and a summary of what was fixed vs. what needs manual attention.

## geno-data-workspaces-init

**Slash command:** `/geno-data-workspaces-init`
  **Arguments:** `[list|<freeform text>]`

> Create data workspaces for personal/life skills (taxes, remodel, career, custom). Scaffolds a directory with metadata, agent context, and links to related workspaces.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` is either a utility subcommand (`list`) or freeform text describing what to work on. If empty, launch the interactive flow.

??? example "Full skill definition (Level 4)"

    # Create Data Workspace
    
    Create data workspaces for personal/life skills that operate on user data, not code. Unlike dev workspaces (which clone repos), data workspaces are lightweight launchpads with metadata linking to where the skill's data actually lives and cross-links to related workspaces.
    
    ## Input
    
    `$ARGUMENTS` is either a utility subcommand (`list`) or freeform text describing what to work on. If empty, launch the interactive flow.
    
    ## Zero Footprint Policy
    
    This skill never modifies a project's tracked files. All geno artifacts (`.geno/`, `CLAUDE.local.md`) live in the workspace directory.
    
    ## Config System
    
    Uses the same `~/.geno/config.yaml` workspace settings as dev workspaces. Auto-created on first use if missing.
    
    ```yaml
    workspaces:
      mode: color
      base_path: "~"
      color:
        default: code-purp
        folders:
          - code-red
          - code-blue
          - code-purp
          - code-indigo
    ```
    
    ## Known Skills
    
    Hard-coded registry of skills with known data paths and workspace conventions (v0.1):
    
    | Skill | Data Path | Structure | Notes |
    |-------|-----------|-----------|-------|
    | `geno-taxes` | `~/docs/finance/taxes/` | `TY{year}/` subdirs | External data, workspace is a launchpad |
    | `geno-remodel` | `~/docs/home/remodel/` | `{project}/` subdirs | External data, workspace is a launchpad |
    | `geno-career` | workspace-local `data/` | `profile.yaml`, `resumes/`, `generated/` | Data lives in workspace; scaffold `data/` on create |
    | Custom | user-specified or none | user-defined | Freeform workspace for any data-oriented task |
    
    ## Central Registry
    
    All data workspaces are tracked in `~/.geno/data-workspaces.yaml`. This file is created on first workspace creation and updated on each subsequent creation.
    
    ```yaml
    version: 1
    workspaces:
      - slug: taxes-2026
        skill: geno-taxes
        path: "~/code-purp/taxes-2026-ws"
        color: code-purp
        status: active
        data_path: "~/docs/finance/taxes/"
        created: 2026-04-26T00:00:00Z
    ```
    
    ## Workflow
    
    ### 1. Load config
    
    - Read `~/.geno/config.yaml`.
    - If the file does not exist, create it with the defaults shown above.
    - Read `mode` to determine the folder strategy.
    - For `color` mode: read `default` folder and `folders` list.
    
    ### 2. Route subcommands
    
    If `$ARGUMENTS` starts with `list`, route to the **list** subcommand (see below) and stop.
    
    If `$ARGUMENTS` is empty, proceed to step 3.
    
    If `$ARGUMENTS` contains a known skill name (e.g., `taxes`, `geno-taxes`, `remodel`, `career`) or freeform text, use it to pre-select the skill and skip the skill selection prompt.
    
    ### 3. Select skill
    
    Use `AskUserQuestion` to ask "Which skill is this data workspace for?" with options:
    
    - **geno-taxes** — Tax filing (data at `~/docs/finance/taxes/`)
    - **geno-remodel** — Home remodel (data at `~/docs/home/remodel/`)
    - **geno-career** — Career toolkit (data in workspace)
    - **Custom** — Custom data workspace
    
    If the user selects "Custom", use `AskUserQuestion` to ask for a brief description of the workspace purpose.
    
    ### 4. Name the workspace
    
    Use `AskUserQuestion` to ask "Name this workspace?" with a suggested default based on the skill:
    
    - **geno-taxes**: suggest `taxes-{current-year}` (e.g., `taxes-2026`)
    - **geno-remodel**: suggest `remodel-{project}` — ask for the project name first
    - **geno-career**: suggest `career-general` or `career-{focus}` — ask for focus area
    - **Custom**: ask for a name
    
    Present the suggested name as the first option (recommended) plus "Custom name" as an alternative.
    
    Slugify the final name: lowercase, hyphens only, 5–25 characters. The workspace directory will be `{slug}-ws`.
    
    ### 5. Select color folder
    
    Use `AskUserQuestion` with the color folders from config. Pre-select the default from `~/.geno/config.yaml`.
    
    Options are the folder names (e.g., `code-red`, `code-blue`, `code-purp`, `code-indigo`). Mark the default as "(Recommended)".
    
    ### 6. Scan registry and cross-link
    
    Read `~/.geno/data-workspaces.yaml` if it exists. If other data workspaces are registered:
    
    Use `AskUserQuestion` with `multiSelect: true` to ask "Include context from other data workspaces?"
    
    Each option shows: `{slug} ({skill}, {color})` with description `Data: {data_path}`.
    
    Selected workspaces will appear in the `includes:` field of `workspace.yaml` and in the "Linked Workspaces" section of `CLAUDE.local.md`.
    
    If no other data workspaces exist, skip this step.
    
    ### 7. Confirm and create
    
    Use `AskUserQuestion` to present the workspace plan with a preview:
    
    ```
    Workspace: {slug}-ws
    Location:  ~/{color}/{slug}-ws/
    Skill:     {skill}
    Data path: {data_path}
    Linked:    {linked-slugs or "none"}
    ```
    
    Options:
    - **Create** (Recommended) — proceed with creation
    - **Change color** — go back to color selection
    - **Change name** — go back to naming
    
    ### 8. Create workspace
    
    #### 8a. Create directory structure
    
    ```bash
    mkdir -p ~/{color}/{slug}-ws/.geno/.workspace
    ```
    
    #### 8b. Write workspace metadata
    
    Write `~/{color}/{slug}-ws/.geno/.workspace/workspace.yaml`:
    
    ```yaml
    type: data
    skill: {skill}
    slug: {slug}
    status: active
    repos: []
    color: {color}
    created: {ISO-8601-timestamp}
    source: skill
    source_ref: {skill}
    data_path: "{data_path}"          # null for custom without a data path
    includes:                          # omit if no cross-links
      - slug: {linked-slug}
        path: "~/{linked-color}/{linked-slug}-ws"
        skill: {linked-skill}
    ```
    
    #### 8c. Write CLAUDE.local.md
    
    Write `~/{color}/{slug}-ws/CLAUDE.local.md`:
    
    ```markdown
    # Data Workspace: {slug}-ws
    
    {description — one sentence about the workspace purpose}
    
    ## Skill
    
    **{skill}** — data at `{data_path}`
    
    ## Linked Workspaces
    
    {For each included workspace:}
    - **{linked-slug}** ({linked-skill}) — `{linked-path}`
      Data: `{linked-data-path}`
    
    {If no links: "No linked workspaces."}
    
    ## Agent Rules
    - Do not commit `.geno/` or `CLAUDE.local.md`.
    - When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
    - This is a **data workspace** — it does not contain git repos to develop.
    - The skill's data lives at `{data_path}`, not in this directory.
    - When reading or writing data for {skill}, use `{data_path}` as the root.
    {If includes: "- Linked workspace data is read-only. Do not modify data in other workspaces without asking."}
    ```
    
    For **geno-career** (workspace-local data), replace data path references with `./data/` and adjust the agent rules:
    
    ```markdown
    ## Skill
    
    **geno-career** — data at `./data/` (local to this workspace)
    
    ## Agent Rules
    - Do not commit `.geno/` or `CLAUDE.local.md`.
    - When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
    - This is a **data workspace** — it does not contain git repos to develop.
    - The `data/` directory contains personal information. Never commit or push it.
    {If includes: "- Linked workspace data is read-only. Do not modify data in other workspaces without asking."}
    ```
    
    #### 8d. Scaffold skill-specific data (career only)
    
    For **geno-career**, create the data directory structure:
    
    ```bash
    mkdir -p ~/{color}/{slug}-ws/data/{resumes,source,generated/resumes,generated/cover-letters}
    ```
    
    For other skills, their data directories already exist at external paths (`~/docs/...`). If the data directory does not exist, create it:
    
    ```bash
    mkdir -p {data_path}
    ```
    
    #### 8e. Update central registry
    
    Read `~/.geno/data-workspaces.yaml`. If it does not exist, create it with:
    
    ```yaml
    version: 1
    workspaces: []
    ```
    
    Append the new workspace entry to the `workspaces` list:
    
    ```yaml
    - slug: {slug}
      skill: {skill}
      path: "~/{color}/{slug}-ws"
      color: {color}
      status: active
      data_path: "{data_path}"
      created: {ISO-8601-timestamp}
    ```
    
    Write the updated file back.
    
    ### 9. Report
    
    Tell the user:
    
    - Workspace created at `~/{color}/{slug}-ws/`
    - Data path: `{data_path}` (or `./data/` for career)
    - Linked workspaces: list each, or "none"
    - Next steps: `cd ~/{color}/{slug}-ws/` and start an agent session to use {skill}
    
    ---
    
    ## Subcommand: list
    
    List all data workspaces.
    
    1. Read `~/.geno/data-workspaces.yaml` if it exists.
    2. Additionally, read `~/.geno/config.yaml` to get color folders. For each color folder, scan for directories ending in `-ws` that have `.geno/.workspace/workspace.yaml` with `type: data`.
    3. Merge: registry entries + scanned entries (deduplicate by path). Scanned entries not in the registry are tagged `[unregistered]`.
    4. Display as a table:
    
    | Workspace | Skill | Color | Data Path | Status | Created | Tags |
    |-----------|-------|-------|-----------|--------|---------|------|
    | `taxes-2026-ws` | geno-taxes | code-purp | `~/docs/finance/taxes/` | active | 2026-04-26 | |
    | `remodel-kitchen-ws` | geno-remodel | code-red | `~/docs/home/remodel/` | active | 2026-04-25 | |
    | `career-general-ws` | geno-career | code-red | (workspace-local) | active | 2026-04-24 | |
    
    Sort: active first, then by creation date (newest first).
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-data-workspaces-init \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = workspace directory created with metadata and registered, or list subcommand completed
    - `failure` = directory creation failed, config unreadable, or registry update failed
    - `abandoned` = user cancelled during confirmation or selection prompts

## geno-icons

**Slash command:** `/geno-icons`
  **Arguments:** `[generate|refine|status] [project-name] [--seeds N] [--prompts 'custom prompt']`

> Generate pixel art icons for geno-ecosystem projects using SD 1.5 + pixel art LoRA.

??? info "Overview (Level 3)"

    ## Commands
    
    Parse the user's arguments to determine the action:
    
    ### `/geno-icons generate [project-name]` or `/geno-icons`
    
    Generate pixel art icon variants for one or all geno-ecosystem projects.
    
    #### Workflow
    
    1. **Set up the venv** (if not already present):
       ```bash
       VENV_DIR="/tmp/geno-icons-venv"
       if [ ! -d "$VENV_DIR" ]; then
         python3.12 -m venv "$VENV_DIR"
         source "$VENV_DIR/bin/activate"
         pip install torch torchvision diffusers transformers accelerate safetensors Pillow peft
       else
         source "$VENV_DIR/bin/activate"
       fi
       ```
    
    2. **Determine target projects.** If a project name is given, generate for that one. Otherwise, scan the ecosystem repos directory for all `geno-*` repos:
       ```
       ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/
       ```
    
    3. **Write and run a generation script.** Use the template below, customizing the `projects` dict with themed prompts for each target project. Write the script to `/tmp/geno-icons-venv/generate.py` and run it.
    
    4. **Output** goes to `/tmp/geno-icons/<project-name>/` with naming: `<NN>_p<prompt-idx>_s<seed>.png`
    
    5. **After generation**, open all non-black images in Preview:
       ```bash
       for f in /tmp/geno-icons/<project>/*.png; do
         size=$(stat -f%z "$f")
         [ "$size" -gt 5000 ] && echo "$f"
       done | xargs open
       ```
       (The NSFW safety filter produces false positive black images — filter by file size >5KB)
    
    6. **Let the user pick.** When they select an image, copy it to the project's `docs/assets/icon.png`:
       ```bash
       mkdir -p "<repo-path>/docs/assets"
       cp "<selected-image>" "<repo-path>/docs/assets/icon.png"
       ```
    
    #### Generation Script Template
    
    ```python
    import torch
    import os
    import time
    from diffusers import StableDiffusionPipeline, DDIMScheduler
    
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float32
    
    print("Loading SD 1.5 pipeline...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=dtype,
    )
    
    print("Loading pixel art LoRA...")
    pipe.load_lora_weights(
        "artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5",
        weight_name="PixelArtRedmond15V-PixelArt-PIXARFK.safetensors",
    )
    
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    
    neg = "blurry, photorealistic, 3d, text, watermark, complex, noisy, border, frame, multiple objects, scenery, landscape, black background"
    
    projects = {
        "project-name": [
            "description of icon concept 1",
            "description of icon concept 2",
            # ... 7 total
        ],
    }
    
    output_base = "/tmp/geno-icons"
    os.makedirs(output_base, exist_ok=True)
    
    for project, base_prompts in projects.items():
        project_dir = os.path.join(output_base, project)
        os.makedirs(project_dir, exist_ok=True)
        img_num = 0
        for prompt_idx, base_prompt in enumerate(base_prompts):
            full_prompt = f"pixelarfk, pixel art, {base_prompt}, white background, game item sprite, centered, clean simple sprite, icon"
            for seed_offset in range(6):
                img_num += 1
                seed = 100 + prompt_idx * 10 + seed_offset
                print(f"  [{img_num}/42] seed={seed} | {base_prompt[:50]}...")
                image = pipe(
                    prompt=full_prompt,
                    negative_prompt=neg,
                    guidance_scale=8.5,
                    num_inference_steps=25,
                    width=512,
                    height=512,
                    generator=torch.Generator(device="cpu").manual_seed(seed),
                ).images[0]
                filename = f"{img_num:02d}_p{prompt_idx}_s{seed}.png"
                image.save(os.path.join(project_dir, filename))
    ```
    
    #### Prompt Design Guidelines
    
    - Frame subjects as **game items, sprites, or RPG inventory icons** — the LoRA excels at these
    - Use **white or light backgrounds** — dark backgrounds trigger the NSFW filter frequently
    - Keep descriptions **concrete and object-focused** — "purple wrench" not "developer tools concept"
    - Always prefix with `pixelarfk, pixel art,` (the LoRA trigger)
    - End with `white background, game item sprite, centered, clean simple sprite, icon`
    
    #### Reference Prompts by Project
    
    | Project | Good prompt themes |
    |---|---|
    | geno-tools | toolbox, Swiss army knife, magic toolkit, treasure chest of tools, mechanical hand with wrench |
    | geno-agents | robot, network nodes, team of small robots, AI brain, radar dish, group of characters |
    | geno-dev | retro computer terminal, wrench + screwdriver, laptop with code, keyboard with glowing keys |
    | geno-media | film camera, microphone, music note + headphones, video player, speaker, paintbrush |
    | geno-research | magnifying glass + book, telescope, laboratory flask, open book with glowing pages, microscope |
    | geno-kaggle | trophy cup, medal, bar chart with arrow, podium, leaderboard |
    | geno-bench | stopwatch, speedometer, racing car, lightning bolt + clock, progress bar |
    | geno-cli | retro TUI window, terminal with sparkles, prompt cursor in a chat bubble, command line wand |
    | geno-iso | shipping container, sealed glass dome, isolation chamber, padlocked box, sandbox border |
    | geno-mon | eye with alert, security camera, heartbeat monitor, radar screen, shield with eye, watchtower |
    | geno-msg | speech bubble, envelope with lightning, chat bubbles, megaphone, carrier pigeon, walkie talkie |
    | geno-notes | notepad with pencil, sticky notes, journal with bookmark, clipboard, quill pen + scroll |
    | geno-term | terminal with cursor, command prompt, CRT monitor, keyboard, matrix rain, retro monitor |
    | geno-vla | eye + neural network, camera lens + AI brain, robotic arm, AR glasses, scanner beam |
    
    ### `/geno-icons refine <project-name> [--prompts 'custom prompt']`
    
    Regenerate icons for a single project with custom or adjusted prompts.
    
    1. Check if `/tmp/geno-icons/<project>/` already has images — show the user what exists
    2. Ask the user what direction to take: new prompts, same prompts with different seeds, or custom prompts
    3. Generate a new batch (use seed range 200+ to avoid collisions with prior runs)
    4. Open results and let the user pick
    
    ### `/geno-icons status`
    
    Show which projects have icons and which don't:
    ```bash
    REPOS_DIR="<ecosystem-repos-path>"
    for repo in "$REPOS_DIR"/geno-* "$REPOS_DIR"/obsidian-*; do
      name=$(basename "$repo")
      if [ -f "$repo/docs/assets/icon.png" ]; then
        echo "  ✓ $name"
      else
        echo "  ✗ $name"
      fi
    done
    ```
    
    ### `/geno-icons animate <project-name>`
    
    Generate an animated GIF from the selected icon using AnimateDiff.
    
    **Note:** AnimateDiff at small sizes produces noisy results. This is experimental. For better animated icons, consider using the static icon as a base and animating with simpler frame interpolation (glow pulse, rotation, etc.) via Pillow/imageio.

??? example "Full skill definition (Level 4)"

    # geno-icons — Pixel Art Icon Generator
    
    Generate 8-bit pixel art icons for geno-ecosystem projects using Stable Diffusion 1.5 with a pixel art LoRA, running locally on MPS (Apple Silicon).
    
    ```!
    python3.12 --version >/dev/null 2>&1 || echo "⚠️ Python 3.12 required (python3.14 has compatibility issues with diffusers)"
    ```
    
    ## Stack
    
    - **Model**: `stable-diffusion-v1-5/stable-diffusion-v1-5` (~2GB)
    - **LoRA**: `artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5` (~50MB)
    - **LoRA weight file**: `PixelArtRedmond15V-PixelArt-PIXARFK.safetensors`
    - **LoRA trigger word**: `pixelarfk`
    - **Device**: MPS (Apple Silicon) or CUDA
    - **Memory**: ~3GB — safe for 24GB machines with normal workloads running
    - **Speed**: ~75 sec/image on MPS at 512x512, 25 steps
    
    ## Dependencies
    
    ```
    torch torchvision diffusers transformers accelerate safetensors Pillow peft
    ```
    
    ## Commands
    
    Parse the user's arguments to determine the action:
    
    ### `/geno-icons generate [project-name]` or `/geno-icons`
    
    Generate pixel art icon variants for one or all geno-ecosystem projects.
    
    #### Workflow
    
    1. **Set up the venv** (if not already present):
       ```bash
       VENV_DIR="/tmp/geno-icons-venv"
       if [ ! -d "$VENV_DIR" ]; then
         python3.12 -m venv "$VENV_DIR"
         source "$VENV_DIR/bin/activate"
         pip install torch torchvision diffusers transformers accelerate safetensors Pillow peft
       else
         source "$VENV_DIR/bin/activate"
       fi
       ```
    
    2. **Determine target projects.** If a project name is given, generate for that one. Otherwise, scan the ecosystem repos directory for all `geno-*` repos:
       ```
       ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/
       ```
    
    3. **Write and run a generation script.** Use the template below, customizing the `projects` dict with themed prompts for each target project. Write the script to `/tmp/geno-icons-venv/generate.py` and run it.
    
    4. **Output** goes to `/tmp/geno-icons/<project-name>/` with naming: `<NN>_p<prompt-idx>_s<seed>.png`
    
    5. **After generation**, open all non-black images in Preview:
       ```bash
       for f in /tmp/geno-icons/<project>/*.png; do
         size=$(stat -f%z "$f")
         [ "$size" -gt 5000 ] && echo "$f"
       done | xargs open
       ```
       (The NSFW safety filter produces false positive black images — filter by file size >5KB)
    
    6. **Let the user pick.** When they select an image, copy it to the project's `docs/assets/icon.png`:
       ```bash
       mkdir -p "<repo-path>/docs/assets"
       cp "<selected-image>" "<repo-path>/docs/assets/icon.png"
       ```
    
    #### Generation Script Template
    
    ```python
    import torch
    import os
    import time
    from diffusers import StableDiffusionPipeline, DDIMScheduler
    
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float32
    
    print("Loading SD 1.5 pipeline...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=dtype,
    )
    
    print("Loading pixel art LoRA...")
    pipe.load_lora_weights(
        "artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5",
        weight_name="PixelArtRedmond15V-PixelArt-PIXARFK.safetensors",
    )
    
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    
    neg = "blurry, photorealistic, 3d, text, watermark, complex, noisy, border, frame, multiple objects, scenery, landscape, black background"
    
    # Customize per project — 7 base prompts × 6 seed variations = 42 variants
    projects = {
        "project-name": [
            "description of icon concept 1",
            "description of icon concept 2",
            # ... 7 total
        ],
    }
    
    output_base = "/tmp/geno-icons"
    os.makedirs(output_base, exist_ok=True)
    
    for project, base_prompts in projects.items():
        project_dir = os.path.join(output_base, project)
        os.makedirs(project_dir, exist_ok=True)
        img_num = 0
        for prompt_idx, base_prompt in enumerate(base_prompts):
            full_prompt = f"pixelarfk, pixel art, {base_prompt}, white background, game item sprite, centered, clean simple sprite, icon"
            for seed_offset in range(6):
                img_num += 1
                seed = 100 + prompt_idx * 10 + seed_offset
                print(f"  [{img_num}/42] seed={seed} | {base_prompt[:50]}...")
                image = pipe(
                    prompt=full_prompt,
                    negative_prompt=neg,
                    guidance_scale=8.5,
                    num_inference_steps=25,
                    width=512,
                    height=512,
                    generator=torch.Generator(device="cpu").manual_seed(seed),
                ).images[0]
                filename = f"{img_num:02d}_p{prompt_idx}_s{seed}.png"
                image.save(os.path.join(project_dir, filename))
    ```
    
    #### Prompt Design Guidelines
    
    - Frame subjects as **game items, sprites, or RPG inventory icons** — the LoRA excels at these
    - Use **white or light backgrounds** — dark backgrounds trigger the NSFW filter frequently
    - Keep descriptions **concrete and object-focused** — "purple wrench" not "developer tools concept"
    - Always prefix with `pixelarfk, pixel art,` (the LoRA trigger)
    - End with `white background, game item sprite, centered, clean simple sprite, icon`
    
    #### Reference Prompts by Project
    
    | Project | Good prompt themes |
    |---|---|
    | geno-tools | toolbox, Swiss army knife, magic toolkit, treasure chest of tools, mechanical hand with wrench |
    | geno-agents | robot, network nodes, team of small robots, AI brain, radar dish, group of characters |
    | geno-dev | retro computer terminal, wrench + screwdriver, laptop with code, keyboard with glowing keys |
    | geno-media | film camera, microphone, music note + headphones, video player, speaker, paintbrush |
    | geno-research | magnifying glass + book, telescope, laboratory flask, open book with glowing pages, microscope |
    | geno-kaggle | trophy cup, medal, bar chart with arrow, podium, leaderboard |
    | geno-bench | stopwatch, speedometer, racing car, lightning bolt + clock, progress bar |
    | geno-cli | retro TUI window, terminal with sparkles, prompt cursor in a chat bubble, command line wand |
    | geno-iso | shipping container, sealed glass dome, isolation chamber, padlocked box, sandbox border |
    | geno-mon | eye with alert, security camera, heartbeat monitor, radar screen, shield with eye, watchtower |
    | geno-msg | speech bubble, envelope with lightning, chat bubbles, megaphone, carrier pigeon, walkie talkie |
    | geno-notes | notepad with pencil, sticky notes, journal with bookmark, clipboard, quill pen + scroll |
    | geno-term | terminal with cursor, command prompt, CRT monitor, keyboard, matrix rain, retro monitor |
    | geno-vla | eye + neural network, camera lens + AI brain, robotic arm, AR glasses, scanner beam |
    
    ### `/geno-icons refine <project-name> [--prompts 'custom prompt']`
    
    Regenerate icons for a single project with custom or adjusted prompts.
    
    1. Check if `/tmp/geno-icons/<project>/` already has images — show the user what exists
    2. Ask the user what direction to take: new prompts, same prompts with different seeds, or custom prompts
    3. Generate a new batch (use seed range 200+ to avoid collisions with prior runs)
    4. Open results and let the user pick
    
    ### `/geno-icons status`
    
    Show which projects have icons and which don't:
    ```bash
    REPOS_DIR="<ecosystem-repos-path>"
    for repo in "$REPOS_DIR"/geno-* "$REPOS_DIR"/obsidian-*; do
      name=$(basename "$repo")
      if [ -f "$repo/docs/assets/icon.png" ]; then
        echo "  ✓ $name"
      else
        echo "  ✗ $name"
      fi
    done
    ```
    
    ### `/geno-icons animate <project-name>`
    
    Generate an animated GIF from the selected icon using AnimateDiff.
    
    **Note:** AnimateDiff at small sizes produces noisy results. This is experimental. For better animated icons, consider using the static icon as a base and animating with simpler frame interpolation (glow pulse, rotation, etc.) via Pillow/imageio.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-icons \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = icon images generated and user selected one (or status report completed)
    - `failure` = venv setup failed, SD pipeline error, or all images were black/unusable
    - `abandoned` = user stopped before selecting an icon

## geno-onboarding

**Slash command:** `/geno-onboarding`

> Walks an operator through onboarding a new skillset into a geno-tools install, including enterprise discovery from GitHub Enterprise, GitLab, Bitbucket, or Gitea.

??? info "Overview (Level 3)"

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
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-onboarding \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = skillset passes audit and is installed via geno-tools install
    - `failure` = repo missing SKILL.md, audit has red flags, or discovery config invalid
    - `abandoned` = user stopped during audit walkthrough or decided not to proceed
    
    ## See also
    
    - `docs/onboarding/index.md` — full onboarding flow
    - `docs/onboarding/audit.md` — reviewer checklist
    - `genotools/discovery.py` — the pluggable provider layer

## geno-skills-create

**Slash command:** `/geno-skills-create`
  **Arguments:** `[skill-name|freeform description]`

> Scaffold a new skill in a geno ecosystem repo. Creates the SKILL.md with proper frontmatter, updates the umbrella skill table and GENO.md skills table.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` is either:
    - A skill name (e.g. `geno-dev-worktrees-manage`) — skip naming, go straight to details
    - Freeform text describing what the skill should do — use it to derive the name
    - Empty — launch the interactive flow
    
    ## Input
    
    `$ARGUMENTS` — {describe expected arguments, or "No arguments." if none}.

??? example "Full skill definition (Level 4)"

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
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-skills-create \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = skill directory and SKILL.md created, umbrella and GENO.md updated
    - `failure` = no geno repo detected, name collision, or file write failed
    - `abandoned` = user stopped during naming, detail gathering, or review

## geno-skills-install

**Slash command:** `/geno-skills-install`
  **Arguments:** `[repo-path|repo-name]`

> Install skills from a local geno ecosystem repo checkout globally via npx skills add. Detects the repo from the current directory, accepts a path or name as an argument, or offers selection when called from a multi-repo workspace.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — one of:
    - **Empty** — detect from context (see Resolution below)
    - **A path** — absolute or relative path to a geno repo checkout
    - **A repo name** — e.g. `geno-dev`, `geno-media` — resolved as a subdirectory of the current workspace

??? example "Full skill definition (Level 4)"

    # geno-skills-install — Install Local Skills Globally
    
    Registers all skills from a local geno ecosystem repo checkout as global slash commands across all supported agents. This is the dev-loop companion to `geno-tools install` — instead of cloning from a remote, it installs from whatever is on disk right now so you can test local changes immediately.
    
    ## When to invoke
    
    - You've edited a SKILL.md and want to pick up the changes in new agent sessions.
    - You've added a new skill directory and need to register it.
    - You want to test a skillset branch before merging.
    - The user says "install these skills", "register skills globally", or "pick up my skill changes".
    
    ## Input
    
    `$ARGUMENTS` — one of:
    - **Empty** — detect from context (see Resolution below)
    - **A path** — absolute or relative path to a geno repo checkout
    - **A repo name** — e.g. `geno-dev`, `geno-media` — resolved as a subdirectory of the current workspace
    
    ## Resolution
    
    ### 1. Explicit argument
    
    If `$ARGUMENTS` is provided:
    
    - If it's an absolute path or starts with `./` or `../`, use it directly. Verify it's a geno repo (has `genotools.yaml` or a `skills/` directory with at least one `SKILL.md`).
    - If it's a repo name (e.g. `geno-dev`), look for it as a subdirectory of the workspace root. The workspace root is the nearest ancestor directory containing `.geno/workspace.yaml`.
    
    ### 2. Inside a geno repo
    
    If no argument is given, check the current working directory and its ancestors for `genotools.yaml` or a `skills/` directory. If found, that's the target repo.
    
    ### 3. Inside a workspace
    
    If no repo is detected in the current directory, look for `.geno/workspace.yaml` in the current directory or its ancestors. Read the `repos:` list.
    
    - **Single repo** — use it automatically. Resolve its path relative to the workspace root.
    - **Multiple repos** — use `AskUserQuestion` to let the user pick:
    
      > Which repo do you want to install skills from?
    
      Options: each repo's `path` value from workspace.yaml (e.g. `geno-dev`, `geno-media`). Include an **All** option to install from every repo.
    
    ### 4. Nothing found
    
    If none of the above match, tell the user:
    
    > Could not detect a geno ecosystem repo. Run this from inside a geno-* repo checkout or pass a path as an argument.
    
    Stop here.
    
    ## Workflow
    
    ### 1. Validate the target
    
    Once the repo path is resolved:
    
    ```bash
    REPO_ROOT="<resolved-path>"
    ```
    
    Verify the repo is a valid geno skillset:
    - Check for `genotools.yaml` at root (read `name` field if present)
    - Check for `skills/` directory
    - Check for at least one `SKILL.md` (root or under `skills/*/`)
    
    If validation fails, report what's missing and stop.
    
    ### 2. Enumerate skills
    
    Find all skill directories that will be registered:
    
    ```bash
    find "$REPO_ROOT/skills" -name "SKILL.md" -mindepth 2 -maxdepth 2 | sort
    ```
    
    Also check for a root-level `SKILL.md`:
    
    ```bash
    test -f "$REPO_ROOT/SKILL.md" && echo "$REPO_ROOT/SKILL.md"
    ```
    
    Print a summary of what will be installed:
    
    ```
    Found N skills to install from geno-{name}:
      - geno-{name} (umbrella)
      - geno-{name}-foo-bar
      - geno-{name}-baz-qux
    ```
    
    ### 3. Install skills globally
    
    For each skill directory, run:
    
    ```bash
    npx --yes skills add "<skill-dir>" --agent '*' --global --yes
    ```
    
    Where `<skill-dir>` is:
    - `$REPO_ROOT` for the root-level SKILL.md (if it exists)
    - `$REPO_ROOT/skills/<skill-name>` for each sub-skill
    
    Run these sequentially and capture output. Report success or failure for each.
    
    ### 4. Handle "All" (multi-repo)
    
    If the user selected **All** in step 3 of Resolution, repeat steps 1–3 for each repo in the workspace. Process repos sequentially and report a combined summary at the end.
    
    ### 5. Report
    
    Print a summary:
    
    ```
    Installed N skills globally from geno-{name} (<path>):
      ✓ geno-{name}
      ✓ geno-{name}-foo-bar
      ✓ geno-{name}-baz-qux
    
    Skills are now available in new agent sessions.
    Current session may need a restart to pick up changes.
    ```
    
    If any failed:
    
    ```
      ✗ geno-{name}-broken — npx error: <message>
    ```
    
    ### 6. Git context (informational)
    
    After installation, show the current git state of the repo for context:
    
    ```bash
    git -C "$REPO_ROOT" log --oneline -1
    git -C "$REPO_ROOT" branch --show-current
    ```
    
    Report:
    
    ```
    Source: branch <branch> @ <short-sha> <commit-message>
    ```
    
    This helps the user know exactly what version of the skills they just installed.
    
    ## Don'ts
    
    - Don't clone or fetch — this skill works on the local checkout as-is.
    - Don't create venvs, bin symlinks, or worktrees — those are `geno-tools install` responsibilities.
    - Don't modify any files in the target repo.
    - Don't use `geno-tools install` — this skill calls `npx skills add` directly because it's registering from a local path, not going through the full install flow.
    - Don't use aliased prefixes like `gt-` in any output — always use canonical `geno-` prefix.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-skills-install \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = all skills registered globally via npx skills add
    - `failure` = no geno repo detected, validation failed, or npx registration errors
    - `abandoned` = user stopped early

## geno-skills-status

**Slash command:** `/geno-skills-status`

> Show the installation status of the geno ecosystem — version, commit, branch, and freshness of each installed skillset.

??? info "Overview (Level 3)"

    ## Input
    
    `$ARGUMENTS` — optional:
    - **Empty** — report on all installed skillsets
    - **A skillset name** (e.g. `geno-dev`, `dev`) — report on just that one in detail

??? example "Full skill definition (Level 4)"

    # geno-skills-status — Ecosystem Installation Status
    
    Shows the current state of every installed geno skillset: version from the manifest, git commit, branch, skill count, and whether the install is behind origin. Also reports the geno-tools version itself and the geno-tools plugin source.
    
    ## When to invoke
    
    - The user asks "what's installed", "what version am I on", "is everything up to date".
    - Before troubleshooting — to see which skillsets are present and at what revision.
    - After running `geno-tools update` to verify results.
    
    ## Input
    
    `$ARGUMENTS` — optional:
    - **Empty** — report on all installed skillsets
    - **A skillset name** (e.g. `geno-dev`, `dev`) — report on just that one in detail
    
    ## Workflow
    
    ### 1. Report geno-tools itself
    
    Get the geno-tools version and source:
    
    ```bash
    geno-tools --version
    ```
    
    Determine where the geno-tools plugin is loaded from. Check the plugin root — this is the repo the agent session loaded geno-tools from. Use `$CLAUDE_PLUGIN_ROOT` if set, otherwise check the known install locations:
    - `~/.claude/plugins/geno-tools/`
    - The current repo if it has `.claude-plugin/plugin.json`
    
    Report:
    
    ```
    geno-tools v{version}
      plugin: {plugin-path}
    ```
    
    ### 2. Enumerate installed skillsets
    
    List all installed skillsets from `~/.geno-tools/`:
    
    ```bash
    ls -d ~/.geno-tools/geno-*/ 2>/dev/null | grep -v geno-bootstrap
    ```
    
    If `$ARGUMENTS` names a specific skillset, filter to just that one. If the named skillset is not installed, report that and stop.
    
    ### 3. Gather per-skillset info
    
    For each installed skillset at `~/.geno-tools/geno-{name}/`:
    
    #### Version and description
    
    Read `genotools.yaml` from the active worktree:
    
    ```bash
    cat ~/.geno-tools/geno-{name}/active/genotools.yaml
    ```
    
    Extract `name`, `version`, and `description`. If the manifest is missing, report "(no manifest)".
    
    #### Git state
    
    From the `main/` worktree:
    
    ```bash
    git -C ~/.geno-tools/geno-{name}/main log --oneline -1
    git -C ~/.geno-tools/geno-{name}/main branch --show-current
    git -C ~/.geno-tools/geno-{name}/main log --format="%ci" -1
    ```
    
    Extract: short SHA, commit message, branch name, commit date.
    
    #### Active variant
    
    Check which variant is active:
    
    ```bash
    readlink ~/.geno-tools/geno-{name}/active
    ```
    
    This is usually `main`. If it points elsewhere, note the variant.
    
    #### Skill count
    
    Count registered skills:
    
    ```bash
    find ~/.geno-tools/geno-{name}/active/skills -name "SKILL.md" -mindepth 2 -maxdepth 2 2>/dev/null | wc -l
    ```
    
    Also check for a root-level `SKILL.md`:
    
    ```bash
    test -f ~/.geno-tools/geno-{name}/active/SKILL.md && echo "+1 umbrella"
    ```
    
    #### Freshness (optional — only when reporting all)
    
    Check if the installed commit is behind origin. This requires a fetch, which is slow, so only do this when the user explicitly asks for freshness or passes a single skillset name:
    
    ```bash
    git -C ~/.geno-tools/geno-{name}/.git fetch --quiet origin 2>/dev/null
    git -C ~/.geno-tools/geno-{name}/main log --oneline HEAD..@{upstream} 2>/dev/null | wc -l
    ```
    
    If behind, report how many commits behind. If the fetch fails (offline, no remote), skip silently.
    
    Only run freshness checks when:
    - A single skillset is specified (`$ARGUMENTS` is not empty)
    - The user explicitly asks about freshness or "is it up to date"
    
    For the all-skillsets overview, skip fetching to keep the report fast.
    
    #### Dependencies
    
    Read `requires:` from `genotools.yaml`:
    
    ```bash
    python3 -c "
    import yaml, sys
    data = yaml.safe_load(open(sys.argv[1]))
    for r in data.get('requires', []):
        print(r)
    " ~/.geno-tools/geno-{name}/active/genotools.yaml 2>/dev/null
    ```
    
    ### 4. Format the report
    
    #### All skillsets (no argument)
    
    Print a summary table:
    
    ```
    geno-tools v0.1.0
    
    Installed skillsets:
    
      Skillset              Version   Commit     Date         Branch   Skills
      ─────────────────────────────────────────────────────────────────────────
      geno-agents           0.1.0     11ac1bb    2026-04-28   main     5
      geno-dev              0.1.0     3eff77d    2026-04-30   main     12
      geno-kaggle           —         f9077a5    2026-04-25   main     4
      geno-media            0.2.0     e582cb0    2026-04-22   main     7
      geno-notes            0.1.0     52c3908    2026-04-29   main     6
      geno-research         0.4.0     34206f5    2026-04-27   main     3
    
      Total: 6 skillsets, 37 skills
    ```
    
    Use aligned columns. Mark skillsets with no `genotools.yaml` version as `—`. If the active variant is not `main`, append `(active: {variant})` to the branch column.
    
    #### Single skillset (with argument)
    
    Print detailed info including freshness and dependencies:
    
    ```
    geno-dev v0.1.0
      Developer and infrastructure utilities — task execution from lab notes,
      git commit history rewriting, worktree management, workspace creation,
      and session forking.
    
      Commit:   3eff77d — Merge pull request #19 from 42euge/feat/gt-snooze
      Date:     2026-04-30
      Branch:   main
      Active:   main
      Remote:   https://github.com/42euge/geno-dev.git
      Freshness: up to date (or: 3 commits behind origin)
    
      Skills (12):
        geno-dev                          (umbrella)
        geno-dev-commits-rewrite
        geno-dev-feature-ship
        geno-dev-issue-work
        geno-dev-loops-cruise
        geno-dev-loops-turbocharge
        geno-dev-prs-check
        geno-dev-scheduling-snooze
        geno-dev-sessions-fork
        geno-dev-tasks-start
        geno-dev-workspaces-init
        geno-dev-worktrees-manage
    
      Dependencies: geno-notes
    ```
    
    List each skill by reading the `skills/` directory names. Mark the umbrella. List dependencies from `requires:` or "none" if empty.
    
    ### 5. Actionable suggestions
    
    After the report, if any issues are detected, suggest next steps:
    
    - Skillsets behind origin: "Run `geno-tools update {name}` to pull latest."
    - Skillsets with no manifest: "Add a `genotools.yaml` to {name} for version tracking."
    - Active variant not `main`: "Switch back with `geno-tools use {name}@main`."
    - Dirty worktree detected: "Uncommitted changes in {name}; `geno-tools update` will skip it."
    
    ## Don'ts
    
    - Don't modify any files — this is a read-only status report.
    - Don't fetch from origin when showing all skillsets — keep the overview fast.
    - Don't use aliased prefixes like `gt-` in output.
    - Don't show geno-bootstrap in the list — it's internal infrastructure.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-skills-status \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = status report printed with version and skill count for all targeted skillsets
    - `failure` = ~/.geno-tools/ missing, specified skillset not found, or geno-tools CLI unavailable
    - `abandoned` = user stopped early

## geno-tools-open-docs

**Slash command:** `/geno-tools-open-docs`

> Open the current repo's GitHub Pages documentation site in the default browser.

??? info "Overview (Level 3)"

    Open the GitHub Pages documentation site for the current repo in the default browser.
    
    ## Behavior
    
    1. Get the GitHub Pages URL for the current repo:
       ```bash
       gh api repos/{owner}/{repo}/pages --jq '.html_url'
       ```
    2. Open it:
       ```bash
       open "$PAGES_URL"
       ```
    3. Print the URL so the user can see it.
    
    If the argument is a subpath (e.g. `/geno-tools-open-docs architecture`), append it to the URL:
    ```bash
    open "${PAGES_URL}architecture/"
    ```
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

    # geno-tools-open-docs — Open Documentation Site
    
    Open the GitHub Pages documentation site for the current repo in the default browser.
    
    ## Behavior
    
    1. Get the GitHub Pages URL for the current repo:
       ```bash
       gh api repos/{owner}/{repo}/pages --jq '.html_url'
       ```
    2. Open it:
       ```bash
       open "$PAGES_URL"
       ```
    3. Print the URL so the user can see it.
    
    If the argument is a subpath (e.g. `/geno-tools-open-docs architecture`), append it to the URL:
    ```bash
    open "${PAGES_URL}architecture/"
    ```
    
    ## Fallback
    
    If `gh api` fails (no Pages configured, not a GitHub repo, etc.), tell the user that GitHub Pages isn't enabled for this repo.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-tools-open-docs \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = docs URL resolved and opened in the browser
    - `failure` = gh api call failed or GitHub Pages not configured for this repo
    - `abandoned` = user stopped early

## geno-tools-update

**Slash command:** `/geno-tools-update`

> Update installed geno ecosystem skillsets to the latest main branch.

??? info "Overview (Level 3)"

    Pull the latest main branch for installed geno-* skillsets, re-register skills, and reinstall venvs if dependencies changed.
    
    ## Usage
    
    Update all installed skillsets:
    ```bash
    geno-tools update
    ```
    
    Update a single skillset:
    ```bash
    geno-tools update <name>
    ```
    
    The `<name>` accepts both full (`geno-dev`) and bare (`dev`) forms.
    
    ## Behavior
    
    For each skillset the command will:
    
    *[...truncated — expand Level 4 for full definition]*

??? example "Full skill definition (Level 4)"

    # geno-tools-update — Update Ecosystem Repos
    
    Pull the latest main branch for installed geno-* skillsets, re-register skills, and reinstall venvs if dependencies changed.
    
    ## Usage
    
    Update all installed skillsets:
    ```bash
    geno-tools update
    ```
    
    Update a single skillset:
    ```bash
    geno-tools update <name>
    ```
    
    The `<name>` accepts both full (`geno-dev`) and bare (`dev`) forms.
    
    ## Behavior
    
    For each skillset the command will:
    1. Fetch from origin
    2. Fast-forward the main worktree to the latest commit
    3. Reinstall the Python venv if `pyproject.toml` changed
    4. Re-register skills via `npx skills add` if any SKILL.md files changed
    
    Skillsets are **skipped** (not errored) when:
    - The worktree has uncommitted changes (dirty)
    - The worktree is on a branch other than the default
    - The skillset is in dev mode (local symlink)
    
    A summary is printed at the end showing updated, up-to-date, skipped, and errored repos.
    
    ## Completion
    
    When this skill finishes, emit a trace:
    
    ```bash
    geno-trace emit \
      --skill geno-tools-update \
      --status <success|failure|abandoned> \
      --tool-calls <approximate count> \
      --errors <count of tool/command errors>
    ```
    
    - `success` = all targeted skillsets updated or confirmed up-to-date
    - `failure` = geno-tools update command errored, fetch failed, or one or more skillsets could not update
    - `abandoned` = user stopped early
