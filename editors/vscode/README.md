# Geno Tools: TT Workspaces

Manage the TT workspace scheme from VS Code. The extension reads TT's
host-owned workspace registries in two views: the workspace open in the current
VS Code window, followed by the complete inventory grouped as:

```text
host
└── track
    └── domain
        └── workspace.2026.q3
            └── repository
```

From the explorer you can:

- open local workspaces and repositories in dedicated VS Code windows;
- open remote entries through VS Code Remote - SSH;
- resume the selected workspace's tmux session with the toolbar or row `+`,
  using live state from TT's host-owned registry and creating it only when no
  registered session exists;
- reopen a specific live tmux session by selecting its row;
- create TT workspaces from a host's context menu and rescan them;
- mirror a workspace to another configured TT host;
- create, list, and remove whole-workspace worktrees; and
- render TT's cross-host workspace report.

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
