# Nomenclature

Naming standard for skills across the geno-ecosystem.

## Hierarchy

| Term | Definition | Example |
|------|-----------|---------|
| **Skillset** | A geno-ecosystem repo | `geno-tools`, `geno-kaggle` |
| **Sub-skillset** | Logical grouping within a skillset | `repos`, `icons`, `benchmarks` |
| **Skill** | Individual capability within a sub-skillset | `scaffold`, `generate`, `run` |

## Naming pattern

```
{skillset}-{sub-skillset}-{skill-slug}
```

### Rules

1. **Skillset** = the repo name (`geno-tools`, `geno-dev`, `geno-kaggle`, etc.)
2. **Sub-skillset** = always a **pluralized noun** (`repos` not `repo`, `tasks` not `task`, `benchmarks` not `benchmark`)
3. **Skill slug** = action verb (`scaffold`, `generate`, `start`, `rewrite`, `run`, `scrape`)
4. **Sub-skillset is always required** — even when a repo has only one skill per group
5. **Umbrella skill** = just `{skillset}` (e.g., `geno-tools`). Every repo has exactly one.

### Slash commands

Slash commands use the canonical skill name directly. The command filename in `commands/` must match the skill name:

| Canonical skill name | Slash command | Command file |
|---------------------|---------------|-------------|
| `geno-tools-repos-scaffold` | `/geno-tools-repos-scaffold` | `geno-tools-repos-scaffold.md` |
| `geno-tools-icons-generate` | `/geno-tools-icons-generate` | — (skill only) |
| `geno-dev-tasks-start` | `/geno-dev-tasks-start` | — (skill only) |
| `geno-kaggle-benchmarks-run` | `/geno-kaggle-benchmarks-run` | — (skill only) |

## Compliant examples

### geno-tools

| Skill name | Sub-skillset | Skill | Notes |
|-----------|-------------|-------|-------|
| `geno-tools` | — | — | umbrella |
| `geno-tools-repos-scaffold` | repos | scaffold | create new geno-* repos |
| `geno-tools-icons-generate` | icons | generate | pixel art icon generation |

### geno-dev (compliant)

| Skill name | Sub-skillset | Skill | Notes |
|-----------|-------------|-------|-------|
| `geno-dev` | — | — | umbrella |
| `geno-dev-tasks-start` | tasks | start | pick up and execute a task |
| `geno-dev-commits-rewrite` | commits | rewrite | clean up git history |

## Cross-ecosystem migration reference

Current names → compliant names for remaining repos. These are targets for future migration, not immediate changes.

### geno-agents

| Current | Compliant |
|---------|-----------|
| `geno-agents-tasks-start` | ✓ already compliant |
| `geno-agents-supercharge` | `geno-agents-loops-supercharge` |

### geno-kaggle

| Current | Compliant |
|---------|-----------|
| `geno-create-benchmark-kaggle` | `geno-kaggle-benchmarks-create` |
| `geno-run-kaggle-bench` | `geno-kaggle-benchmarks-run` |
| `geno-upload-kaggle` | `geno-kaggle-notebooks-upload` |
| `geno-kaggle-discussion` | `geno-kaggle-discussions-scrape` |
| `geno-kaggle-benchmarks-task-generate` | `geno-kaggle-benchmarks-generate` |
| `geno-kaggle-benchmarks-task-review` | `geno-kaggle-benchmarks-review` |

### geno-taxes

| Current | Compliant |
|---------|-----------|
| `geno-tax-status` | `geno-taxes-filings-status` |
| `geno-tax-parse` | `geno-taxes-documents-parse` |
| `geno-tax-summary` | `geno-taxes-filings-summarize` |
| `geno-tax-checklist` | `geno-taxes-documents-checklist` |
| `geno-tax-fetch` | `geno-taxes-documents-fetch` |

### geno-media

| Current | Compliant |
|---------|-----------|
| `geno-media-audiobook-create` | `geno-media-audiobooks-create` |
| `geno-media-audiobook-recursive` | `geno-media-audiobooks-recursive` |
| `geno-media-video-create` | `geno-media-videos-create` |
| `geno-media-podcast-create` | `geno-media-podcasts-create` |
| `geno-media-audio-upload` | `geno-media-uploads-audio` |
| `geno-media-tts-config` | `geno-media-configs-tts` |
| `geno-media-stt-config` | `geno-media-configs-stt` |

### geno-research

| Current | Compliant |
|---------|-----------|
| `geno-research-paper-generate` | `geno-research-papers-generate` |
| `geno-research-repo-docs` | `geno-research-docs-generate` |
| `geno-research-deep` | `geno-research-topics-deep` |
| `geno-research-notes` | `geno-research-notes-manage` |
| `geno-research-supercharge` | `geno-research-loops-supercharge` |
