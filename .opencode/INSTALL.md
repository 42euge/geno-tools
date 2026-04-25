# Installing geno-tools for OpenCode

## 1. Add the plugin

In your `opencode.json`:

```json
{
  "plugins": [
    "geno-tools@git+https://github.com/42euge/geno-tools.git"
  ]
}
```

## 2. Install the Python CLI

```bash
pipx install git+https://github.com/42euge/geno-tools.git
```

## 3. Restart OpenCode

The plugin registers geno-tools skills automatically on startup.
