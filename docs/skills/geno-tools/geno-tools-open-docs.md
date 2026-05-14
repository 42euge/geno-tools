---
title: geno-tools-open-docs
description: Open the current repo's GitHub Pages documentation site in the default browser
---

# geno-tools-open-docs

`/geno-tools-open-docs`

> Open the current repo's GitHub Pages documentation site in the default browser

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

Open the GitHub Pages documentation site for the current repo in the default browser.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

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

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Error recovery section** — LLMs can get stuck in retry loops or abandon tasks on first failure. Explicit fallback steps prevent both.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
