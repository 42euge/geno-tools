# Geno Tools: TT Workspaces

Manage the TT workspace scheme from VS Code. The extension reads TT's
host-owned workspace registries in two views: the workspace open in the current
VS Code window, followed by the complete inventory grouped as:

```text
host
└── track
    └── domain
        └── workspace.2026.q3
            ├── Repositories
            │   └── repository
            ├── tmux Sessions
            │   └── session
            └── VS Code Terminals
                └── terminal
```

From the explorer you can:

- open a workspace in the current window or a new window using adjacent row
  actions, while repositories continue to honor `genoTools.openInNewWindow`;
- open remote entries through VS Code Remote - SSH;
- create a workspace from the view-title `+`;
- initialize an empty Git repository from the `Repositories` group `+`;
- create a tmux session from the `tmux Sessions` group `+`, optionally choosing
  its name or letting the extension generate the next available name; the
  registry and both trees refresh before the new session is attached;
- refresh and focus open integrated terminals from the `VS Code Terminals`
  group;
- recover an unlinked integrated terminal into tmux with the row's robot
  button: after explicit consent, the extension samples the full available
  scrollback within a 60,000-character bound, matches it locally to a saved
  Claude or Codex conversation, asks an OpenAI Agents SDK planner for a typed
  name and summary, restores the clipboard, and lets you create, rename, or
  cancel the reviewed resume proposal;
- see `tmux: <session>` on linked terminal rows and `VS Code` on tmux rows that
  are currently attached in an integrated terminal;
- browse repositories and live tmux sessions in separate workspace folders;
- reopen a specific live tmux session by selecting its row;
- delete a tmux session with its trash action after confirming the destructive
  operation;
- create TT workspaces from a host's context menu and rescan them;
- mirror a workspace to another configured TT host;
- create, list, and remove whole-workspace worktrees; and
- render TT's cross-host workspace report.

Each view title shows the running extension version and its UTC build datetime,
so an installed build can be distinguished from an older cached copy.

## Requirements

Install `geno-tt` and configure at least one host:

```sh
geno-tools install geno-tt
tt hosts
```

Remote entries require the VS Code **Remote - SSH** extension and working SSH
access to the configured host. The extension invokes `tt` without a shell. Set
`genoTools.ttPath` if it is not on VS Code's PATH; the default also checks
`~/.local/bin/tt`.

AI recovery reads its provider from `~/.geno/config.yaml` by default:

```yaml
llm:
  endpoint: https://api.openai.com/v1
  model: gpt-5.6
  api_key_env: OPENAI_API_KEY
  api: responses
```

The credential remains in the named environment variable; do not put the token
in YAML. `genoTools.agentConfigPath` selects another YAML file, while a nonempty
`genoTools.agentModel` overrides only the configured model. When the file or an
individual field is absent, the extension falls back to `OPENAI_BASE_URL`,
`OPENAI_DEFAULT_MODEL`, and `OPENAI_API_KEY`.

Before calling OpenAI, recovery rarity-matches the captured scrollback against
`~/.claude/projects` and `~/.codex/sessions`. No tmux session is created unless
a saved conversation matches confidently. The extension constructs the exact
`clauded -r <session-id>` or `codexd resume <session-id>` command locally and
shows the agent, validated ID, score, and command for confirmation; the model
cannot provide a session ID or startup command.

The recovery agent has no mutation tools and SDK tracing is disabled. Its
structured name, summary, and workspace path are validated before tmux is
created. Terminal history is limited to 60,000 characters sampled
chronologically across the full available scrollback and is sent only after the
confirmation dialog, which also identifies the resolved endpoint, model, and
credential variable. Saved Claude and Codex transcripts stay local.

## Development

```sh
cd editors/vscode
npm install
npm run check
npm test
npm run build
```

Open this directory in VS Code and run the **Extension** launch configuration,
or package a VSIX with `npm run package`.
