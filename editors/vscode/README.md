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
                ├── ┌ terminal
                ├── └ terminal
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
  extension records the session as managed, then refreshes the registry and
  both trees before attaching;
- refresh and focus open integrated terminals from the `VS Code Terminals`
  group, with split terminals shown in VS Code's native order and using its
  `┌`, `├`, and `└` markers;
- name one unmanaged integrated terminal with AI using its bounded scrollback,
  or name every eligible terminal in the group with one action;
- recover an unlinked integrated terminal into tmux with the row's robot
  button: after explicit consent, the extension samples the full available
  scrollback within a 60,000-character bound, matches it locally to a saved
  Claude or Codex conversation, asks an OpenAI Agents SDK planner for a typed
  name and summary, restores the clipboard, and lets you create, rename, or
  cancel the reviewed resume proposal;
- see `tmux: <session>` on linked terminal rows and `VS Code` on tmux rows that
  are currently attached in an integrated terminal;
- browse repositories and live or stopped managed tmux sessions in separate
  workspace folders;
- reopen a specific live tmux session by selecting its row;
- adopt a live `External` workspace session with **Manage tmux Session** when
  TT should own its future lifecycle;
- restore a stopped managed session to its saved directory, including the
  validated Claude or Codex resume command when it came from terminal recovery;
- remove a managed session with its trash action after confirming the
  destructive operation, even when the tmux session or entire server is already
  gone;
- create TT workspaces from a host's context menu and rescan them;
- mirror a workspace to another configured TT host with one host choice;
- dispatch work from an existing mirror using an editor selection, active
  document, brief instruction, or Markdown handoff;
- create a verified ZIP on the originating host and retire a remote mirror from
  the mirror row's trash action;
- open remote dispatch sessions, safely recall completed work, and open the
  returned `RETURN.md` handoff;
- create, list, and remove whole-workspace worktrees; and
- render TT's cross-host workspace report.

Each view title shows the running extension version and its UTC build datetime,
so an installed build can be distinguished from an older cached copy.

## tmux lifecycle

The extension distinguishes three session states:

- **Live** sessions were created or adopted by the extension and still exist in
  the host's current tmux state. They can be reopened or removed.
- **Stopped** sessions have a saved managed record but are absent from a
  successful host scan. They can be restored or removed. A crashed tmux server
  therefore leaves recoverable rows instead of trapping stale live rows.
- **External** sessions are live workspace sessions that the extension does not
  own. They can be reopened, but lifecycle actions remain disabled until you
  explicitly choose **Manage tmux Session**.

The first tree load, explicit refreshes, and lifecycle actions scan live state;
the extension does not poll continuously. If a local or remote host cannot be
scanned, its state is unknown: the view reports the real connection error and
keeps managed records unchanged rather than marking them stopped.

Remove is convergent. It attempts `tmux kill-session`, but treats tmux's narrow
"no server running", "no sessions", and "can't find session" responses as an
already-completed removal. SSH, authorization, cancellation, missing executable,
and other failures remain visible errors and preserve the managed record.

## Requirements

Install `geno-tt` 0.9.0 or newer and configure at least one remote host:

```sh
geno-tools install geno-tt
tt hosts
```

Remote entries require the VS Code **Remote - SSH** extension and working SSH
access to the configured host. The extension invokes `tt` without a shell. Set
`genoTools.ttPath` if it is not on VS Code's PATH; the default also checks
`~/.local/bin/tt`.

The extension declares itself as a VS Code UI extension. In a Remote - SSH
window it continues running from the Mac installation and controls the local
`tt` CLI; a second copy of this VSIX is not required on the SSH host.

Split-terminal markers are intentionally implemented through unsupported VS
Code internals: the public extension API does not expose native terminal group
membership, so Geno Tools uses `sqlite3` to read `terminal.integrated.layoutInfo`
from the window's private `state.vscdb`. This may break across VS Code releases.
If `sqlite3`, the database, or its expected schema is unavailable, the terminal
list remains usable and simply falls back to ungrouped rows.

AI naming and recovery read their provider from `~/.geno/config.yaml` by
default:

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

`Name with AI` immediately asks the configured backend for a unique
one-to-three-word tag and renames the integrated terminal. `Name All with AI`
immediately processes eligible terminals in order and continues if one terminal
cannot be named. Bulk naming is conservative: it accepts common default titles
such as `zsh`, `codex`, and `claude`, while skipping custom or explicitly
assigned titles, terminals already named by the extension, and terminals linked
to tmux. The per-terminal action remains an explicit override for any unmanaged
terminal.

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

## Remote mirrors and dispatch

Use the **Mirror Workspace to Host** button directly on a local workspace row,
beside its open buttons. Choose a configured host and the extension creates the
same workspace on that host with rsync, including Git metadata and current
working state. No task name or agent handoff is needed. TT worktrees are
excluded because their Git metadata contains source-machine paths.

The **Remote Mirrors** section sits directly below **Current Workspace**, with
**All Workspaces** at the bottom. Both secondary sections start collapsed;
Remote Mirrors opens automatically when the current workspace has a mirror.
Before mirroring it explains where to start; afterward each row represents the
same stable TT workspace ID on another host. Select a row to open that mirror
in a new VS Code window, or use its rocket action to **Dispatch Work to This
Mirror**. The adjacent trash action is **Back Up and Retire Mirror**. It asks
for modal confirmation, invokes the focused TT retirement path, and refreshes
the section only after the remote workspace has moved.

Retiring a mirror is backup-first. `tt` archives the complete remote workspace,
copies the ZIP into `~/.geno/tt/backups/mirrors/` on the machine that created
the mirror, and verifies SHA-256 before moving the remote workspace into its
graveyard. Archive, transfer, or checksum failure leaves the mirror active.

Dispatch is the separate task-level operation. It asks for a durable task name
and the remote agent's context from:

- the active editor selection;
- the complete active document;
- a short instruction; or
- a Markdown/text handoff file.

The extension sends that text to `tt dispatch` over stdin. `geno-tt` remains
responsible for Git-state transfer, the isolated remote worktree, tmux startup,
local-drift detection, and recall safety.

Use **Manage Remote Dispatches** to reopen an active tmux session, recall an
already stopped session, stop and recall an active session, or open the returned
`RETURN.md`. **Stop and Recall** terminates the remote tmux session and therefore
always requires confirmation.

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
