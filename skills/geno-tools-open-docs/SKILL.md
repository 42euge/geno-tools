---
name: geno-tools-open-docs
description: >-
  Open the current repo's GitHub Pages documentation site in the default browser.
  Use when user says /geno-tools-open-docs or asks to open/view the
  docs website.
allowed-tools: "Bash(open *) Bash(gh api *) Bash(git *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
observability:
  success_signal: "GitHub Pages URL resolved and opened in the default browser"
  failure_signals:
    - "gh api failed (no GitHub Pages configured or not a GitHub repo)"
    - "open command failed"
  knowledge_reads: []
  knowledge_writes: []
---

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
