# Getting Started

## Install this skillset in your agent

`geno-tools` is a skills-only repo. Choose your agent and install the plugin package directly.

=== "Claude Code"

```text
/plugin marketplace add 42euge/geno-tools
/plugin install geno-tools@geno-tools
```

=== "Antigravity CLI"

```bash
agy plugin install https://github.com/42euge/geno-tools
```

=== "Codex"

```text
/plugin marketplace add 42euge/geno-tools
/plugins
```

=== "OpenCode"

```json
{
  "plugins": ["geno-tools@git+https://github.com/42euge/geno-tools.git"]
}
```

=== "Cursor"

Install via Cursor's plugin manager (it reads `.cursor-plugin/plugin.json`) or add this repo to your plugin directory.

## Use it

- Open the installed skillset docs from the agent surface (`/geno-tools-open-docs`), or
- browse the web docs at <https://42euge.github.io/geno-tools/>

## About changes

This repo does not provide or require a Python CLI (`geno-tools` shell command). It only provides `skills/` and plugin metadata that agents can load.
