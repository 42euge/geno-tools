# CI Template

GitHub Actions workflow that builds the MkDocs Material site and deploys it to GitHub Pages. Identical for every geno-* skillset repo. No variable substitution.

## `.github/workflows/docs.yml`

```yaml
name: Deploy docs to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: pip install mkdocs-material
      - run: mkdocs build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

## After first push

Enable GitHub Pages on the new repo so the workflow's deployment target exists:

```bash
gh api repos/42euge/$REPO/pages -X POST -f build_type=workflow 2>/dev/null || true
```

The `|| true` makes this idempotent — if Pages is already enabled the call returns 422 and we move on.
