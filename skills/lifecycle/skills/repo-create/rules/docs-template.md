# Docs Template

MkDocs Material site scaffold and the `.specs/` planning files. The orchestrator substitutes `$REPO` and `$DESCRIPTION` when rendering each template.

## `mkdocs.yml`

```yaml
site_name: $REPO
site_description: $DESCRIPTION
site_url: https://42euge.github.io/$REPO/
repo_url: https://github.com/42euge/$REPO
repo_name: 42euge/$REPO

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
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.top
    - content.code.copy
    - content.code.annotate
    - search.highlight
    - search.suggest
    - toc.follow

nav:
  - Home: index.md
  - Getting Started: getting-started.md

extra_css:
  - stylesheets/extra.css

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
  - md_in_html
  - def_list
  - toc:
      permalink: true

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/42euge
  generator: false
```

## `docs/index.md`

```markdown
# $REPO

$DESCRIPTION

## Installation

\`\`\`bash
geno-tools install $REPO
\`\`\`

## Quick Start

See [Getting Started](getting-started.md) for usage instructions.

## Links

- [GitHub](https://github.com/42euge/$REPO)
- [Docs](https://42euge.github.io/$REPO/)
```

## `docs/getting-started.md`

```markdown
# Getting Started

## Prerequisites

- [geno-tools](https://github.com/42euge/geno-tools) installed

## Installation

\`\`\`bash
geno-tools install $REPO
\`\`\`

## Usage

Run `/$REPO` to get started.
```

## `docs/stylesheets/extra.css`

```css
:root {
  --md-primary-fg-color: #1a0a2e;
  --md-primary-fg-color--light: #2d1b4e;
  --md-primary-fg-color--dark: #0f0619;
  --md-accent-fg-color: #e8650a;
}
[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #1a0a2e;
  --md-accent-fg-color: #f0923a;
  --md-default-bg-color: #0e0b14;
}
.md-header {
  background: linear-gradient(135deg, #1a0a2e 0%, #2d1050 50%, #3a1560 100%);
}
.md-tabs {
  background: linear-gradient(135deg, #0f0619 0%, #1a0a2e 100%);
}
.md-footer {
  background: linear-gradient(135deg, #0f0619, #1a0a2e);
}
```

## `.specs/VISION.md`

```markdown
# Vision

$DESCRIPTION

## Why this exists

<!-- What problem does $REPO solve? Who benefits? -->

## Where we're headed

<!-- What does the world look like when $REPO succeeds? -->
```

## `.specs/GOALS.md`

```markdown
# Goals

Current goals for $REPO. Review and update regularly.

## Active

- <!-- Goal 1: description, target date -->

## Completed

- <!-- Moved here when done -->

## Deferred

- <!-- Moved here when deprioritized -->
```

## `.specs/TENETS.md`

```markdown
# Tenets

Architectural principles that guide development decisions in $REPO. When tenets conflict, earlier entries take precedence.

1. **<!-- Tenet 1 -->** — <!-- Description -->
2. **<!-- Tenet 2 -->** — <!-- Description -->
3. **<!-- Tenet 3 -->** — <!-- Description -->
```

## `.specs/features/.gitkeep`

```bash
mkdir -p .specs/features && touch .specs/features/.gitkeep
```
