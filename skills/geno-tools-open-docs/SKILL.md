---
name: geno-tools-open-docs
description: >-
  Open the geno-tools documentation website in the default browser.
  Use when user says /geno-tools-open-docs, /gt-open-docs, or asks to
  open/view the geno-tools docs site.
allowed-tools: "Bash(open *) Bash(gh api *) Bash(git remote *)"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-tools-open-docs — Open Documentation Site

Open the geno-tools GitHub Pages documentation site in the default browser.

## Behavior

1. Determine the docs URL from the git remote:
   ```bash
   REMOTE_URL=$(git -C ~/.geno-tools/geno-tools/active remote get-url origin 2>/dev/null \
     || git remote get-url origin 2>/dev/null \
     || echo "https://github.com/42euge/geno-tools")
   ```
2. Derive the GitHub Pages URL from the remote (e.g. `42euge/geno-tools` → `https://42euge.github.io/geno-tools/`).
3. Open it:
   ```bash
   open "$PAGES_URL"
   ```
4. Print the URL so the user can see it.

If the argument is a subpath (e.g. `/geno-tools-open-docs architecture`), append it to the URL:
```bash
open "https://42euge.github.io/geno-tools/architecture/"
```

## Fallback

If the remote can't be resolved, use the hardcoded URL: `https://42euge.github.io/geno-tools/`
