# VS Code Extension

**Geno Tools: TT Workspaces** brings local and remote TT workspaces into the
VS Code activity bar. It can open repositories, manage tmux sessions, mirror
workspaces, dispatch remote work, and organize integrated terminals.

## Requirements

- VS Code 1.96 or newer
- `geno-tt` 0.9.0 or newer
- Node.js and npm to package the extension
- VS Code Remote - SSH and working SSH access for remote workspaces

Install `geno-tt` and confirm that TT can read your host configuration:

```zsh
geno-tools install geno-tt
tt hosts
```

## 1. Package the extension

The extension currently ships from this repository as a VSIX. Clone the repo,
install its extension dependencies, and create the package:

```zsh
git clone https://github.com/42euge/geno-tools.git
cd geno-tools/editors/vscode
npm install
npm run package
```

The package command checks the TypeScript, runs the extension tests, builds the
production bundle, and creates `geno-tools-tt-workspaces-<version>.vsix`.

## 2. Install the VSIX

From the same directory:

```zsh
code --install-extension geno-tools-tt-workspaces-*.vsix
```

You can also open the Extensions view in VS Code, choose **Views and More
Actions (…) → Install from VSIX…**, and select the generated file. Reload VS
Code when prompted.

The extension is a UI extension. In a Remote - SSH window it keeps running from
your local VS Code installation and controls the local `tt` CLI, so you do not
need to install the VSIX again on the remote host.

## 3. Open Geno Tools

Select the Geno Tools icon in the activity bar. The extension shows:

- **Current Workspace** — the workspace open in this window
- **Remote Mirrors** — copies of the current workspace on configured hosts
- **All Workspaces** — the complete host, track, domain, and workspace tree

Use the refresh button or run **Geno Tools: Rescan TT Workspaces** from the
Command Palette after changing TT configuration.

## 4. Configure the TT executable

No setting is normally required. The extension searches VS Code's `PATH` and
then `~/.local/bin/tt`. If VS Code still cannot find TT, copy the result of
`command -v tt` into your user settings as an absolute path:

```json
{
  "genoTools.ttPath": "/absolute/path/to/tt",
  "genoTools.openInNewWindow": true
}
```

Open **Geno Tools: Show TT Output** from the Command Palette to inspect command
output and connection errors.

## 5. Optional AI naming and recovery

Terminal naming and tmux recovery use the provider configured in
`~/.geno/config.yaml`:

```yaml
llm:
  endpoint: https://api.openai.com/v1
  model: gpt-5.6
  api_key_env: OPENAI_API_KEY
  api: responses
```

Keep the credential in the named environment variable; do not put the token in
YAML. Set `genoTools.agentConfigPath` to use another config file or
`genoTools.agentModel` to override only the model.

The extension asks for confirmation before sending terminal history for
recovery. Saved Claude and Codex transcripts remain local.

## What to try next

- Create a workspace with the view-title **+** button.
- Open a repository in the current window or a new window.
- Create, reopen, restore, or remove a managed tmux session.
- Mirror a workspace to a configured remote host.
- Use **Name with AI** on an unmanaged integrated terminal.

See the
[extension README](https://github.com/42euge/geno-tools/tree/main/editors/vscode#readme)
for the complete feature and lifecycle reference.
