import { homedir } from "node:os";
import { dirname, join, relative, sep } from "node:path";

import * as vscode from "vscode";

import { TtDispatch, TtHost, workspaceReference } from "./model";
import { TtCli } from "./ttCli";
import { WorkspaceNode, WorkspaceTreeProvider } from "./workspaceTree";

const SAFE_DISPATCH_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export async function dispatchWorkspaceToHost(
  cli: TtCli,
  provider: WorkspaceTreeProvider,
  source: WorkspaceNode,
  destinationHost?: TtHost
): Promise<void> {
  if (!isLocal(source.host, source.registry.host)) {
    throw new Error(
      "Dispatch must start from a local TT workspace. Open or recall the workspace locally first."
    );
  }
  const hosts = (await provider.hosts()).filter(
    (host) => host.alias !== source.host.alias && host.hostname !== "localhost"
  );
  if (hosts.length === 0) {
    throw new Error("Configure a remote TT host before dispatching a workspace.");
  }
  const destination = destinationHost
    ? hosts
        .filter((host) => host.alias === destinationHost.alias)
        .map((host) => ({
          label: host.alias,
          description: host.hostname,
          host
        }))[0]
    : await vscode.window.showQuickPick(
        hosts.map((host) => ({
          label: host.alias,
          description: host.hostname,
          host
        })),
        {
          title: `Dispatch ${workspaceReference(source.workspace)}`,
          placeHolder: "Choose the remote host"
        }
      );
  if (!destination) {
    if (destinationHost) {
      throw new Error("The selected remote mirror is no longer configured.");
    }
    return;
  }
  const name = await dispatchNameInput(source.workspace.name);
  if (!name) {
    return;
  }
  const handoff = await pickDispatchContext();
  if (!handoff) {
    return;
  }
  const confirmation = await vscode.window.showWarningMessage(
    `Dispatch ${workspaceReference(source.workspace)} to ${destination.host.alias} as '${name}' using ${handoff.description}?`,
    { modal: true },
    "Dispatch"
  );
  if (confirmation !== "Dispatch") {
    return;
  }
  const sourcePath = activeWorkspaceView(source.workspace.path);

  await cli.run(
    [
      "dispatch",
      destination.host.alias,
      "--name",
      name,
      "--workspace",
      sourcePath,
      "--context-file",
      "-"
    ],
    `Dispatching ${workspaceReference(source.workspace)} to ${destination.host.alias}`,
    { cwd: sourcePath, input: handoff.text }
  );
  const action = await vscode.window.showInformationMessage(
    `Dispatched '${name}' to ${destination.host.alias}.`,
    "Open Remote Session",
    "Manage Dispatches"
  );
  if (action === "Open Remote Session") {
    await openDispatchSession(cli, destination.host, dispatchSessionName(name));
  } else if (action === "Manage Dispatches") {
    await manageDispatches(cli, name);
  }
}

export async function manageDispatches(
  cli: TtCli,
  preferredName?: string
): Promise<void> {
  const dispatches = await cli.dispatches();
  if (dispatches.length === 0) {
    await vscode.window.showInformationMessage("No TT dispatches found on this Mac.");
    return;
  }
  const items = dispatches.map((dispatch) => ({
    label: dispatch.name,
    description: `${dispatch.status} · ${dispatch.target.host_alias}`,
    detail: dispatch.source.workspace_view,
    dispatch
  }));
  const picked = preferredName
    ? items.find((item) => item.dispatch.name === preferredName)
    : await vscode.window.showQuickPick(items, {
        title: "Manage Remote Dispatches",
        placeHolder: "Choose a dispatch",
        matchOnDescription: true,
        matchOnDetail: true
      });
  if (!picked) {
    return;
  }

  if (picked.dispatch.status === "active") {
    const action = await vscode.window.showQuickPick(
      [
        { label: "Open Remote Session", action: "open" },
        {
          label: "Recall",
          description: "Remote tmux must already be stopped",
          action: "recall"
        },
        {
          label: "Stop and Recall",
          description: "Ends remote tmux, then restores locally",
          action: "stop"
        }
      ],
      { title: picked.dispatch.name, placeHolder: "Choose an action" }
    );
    if (!action) {
      return;
    }
    if (action.action === "open") {
      await openDispatchSession(
        cli,
        await dispatchHost(cli, picked.dispatch),
        picked.dispatch.session
      );
      return;
    }
    await recallFromEditor(cli, picked.dispatch, action.action === "stop");
    return;
  }

  if (picked.dispatch.return_file) {
    await openReturnHandoff(picked.dispatch.return_file);
    return;
  }
  await vscode.window.showInformationMessage(
    `Dispatch '${picked.dispatch.name}' is ${picked.dispatch.status}.`
  );
}

async function recallFromEditor(
  cli: TtCli,
  dispatch: TtDispatch,
  stop: boolean
): Promise<void> {
  if (stop) {
    const confirmation = await vscode.window.showWarningMessage(
      `Stop '${dispatch.session}' on ${dispatch.target.host_alias} and recall '${dispatch.name}'?`,
      { modal: true },
      "Stop and Recall"
    );
    if (confirmation !== "Stop and Recall") {
      return;
    }
  }
  await cli.run(
    ["recall", dispatch.name, ...(stop ? ["--stop"] : [])],
    `Recalling ${dispatch.name}`
  );
  const recalled = (await cli.dispatches()).find(
    (record) => record.name === dispatch.name
  );
  if (recalled?.return_file) {
    const action = await vscode.window.showInformationMessage(
      `Recalled '${dispatch.name}' into ${recalled.source.workspace_view}.`,
      "Open Return Handoff"
    );
    if (action === "Open Return Handoff") {
      await openReturnHandoff(recalled.return_file);
    }
  } else {
    await vscode.window.showInformationMessage(`Recalled '${dispatch.name}'.`);
  }
}

async function openDispatchSession(
  cli: TtCli,
  host: TtHost,
  sessionName: string
): Promise<void> {
  const terminal = vscode.window.createTerminal({
    name: `TT Dispatch: ${host.alias}/${sessionName}`,
    cwd: homedir()
  });
  terminal.show();
  terminal.sendText(await cli.openDispatchCommand(host, sessionName));
}

async function dispatchHost(cli: TtCli, dispatch: TtDispatch): Promise<TtHost> {
  return (await cli.hosts()).find((host) => host.alias === dispatch.target.host_alias) ?? {
    alias: dispatch.target.host_alias,
    hostname: dispatch.target.hostname,
    isDefault: false
  };
}

async function openReturnHandoff(path: string): Promise<void> {
  const document = await vscode.workspace.openTextDocument(vscode.Uri.file(path));
  await vscode.window.showTextDocument(document);
}

async function dispatchNameInput(workspaceName: string): Promise<string | undefined> {
  const timestamp = new Date().toISOString().replace(/\D/g, "").slice(0, 14);
  return vscode.window.showInputBox({
    title: "Dispatch Workspace",
    prompt: "Durable dispatch name used for tmux and later recall",
    value: `${workspaceName}-${timestamp}`,
    validateInput: (value) =>
      SAFE_DISPATCH_NAME.test(value)
        ? undefined
        : "Use letters, digits, dots, underscores, and hyphens."
  });
}

interface DispatchContext {
  text: string;
  description: string;
}

async function pickDispatchContext(): Promise<DispatchContext | undefined> {
  const editor = vscode.window.activeTextEditor;
  const choices: Array<{
    label: string;
    description?: string;
    mode: "selection" | "document" | "input" | "file";
  }> = [];
  if (editor && !editor.selection.isEmpty) {
    choices.push({
      label: "Use Active Selection",
      description: editor.document.fileName,
      mode: "selection"
    });
  }
  if (editor) {
    choices.push({
      label: "Use Active Document",
      description: editor.document.fileName,
      mode: "document"
    });
  }
  choices.push(
    { label: "Enter Brief Instruction", mode: "input" },
    { label: "Choose Markdown Handoff", mode: "file" }
  );
  const picked = await vscode.window.showQuickPick(choices, {
    title: "Dispatch Context",
    placeHolder: "Choose what the remote agent should receive"
  });
  if (!picked) {
    return undefined;
  }

  if (picked.mode === "selection" && editor) {
    return nonemptyDispatchContext(
      editor.document.getText(editor.selection),
      "the active editor selection"
    );
  }
  if (picked.mode === "document" && editor) {
    return nonemptyDispatchContext(
      editor.document.getText(),
      `the active document ${editor.document.fileName}`
    );
  }
  if (picked.mode === "input") {
    const text = await vscode.window.showInputBox({
      title: "Dispatch Context",
      prompt: "What should the remote agent accomplish?",
      placeHolder: "Implement and verify…",
      ignoreFocusOut: true,
      validateInput: (value) => value.trim() ? undefined : "Enter an instruction."
    });
    return text === undefined
      ? undefined
      : nonemptyDispatchContext(text, "the entered instruction");
  }

  const files = await vscode.window.showOpenDialog({
    title: "Choose Dispatch Handoff",
    canSelectMany: false,
    canSelectFiles: true,
    canSelectFolders: false,
    filters: { "Markdown and text": ["md", "markdown", "txt"] }
  });
  if (!files?.[0]) {
    return undefined;
  }
  const text = new TextDecoder().decode(await vscode.workspace.fs.readFile(files[0]));
  return nonemptyDispatchContext(text, `the handoff ${files[0].fsPath}`);
}

function nonemptyDispatchContext(text: string, description: string): DispatchContext {
  if (!text.trim()) {
    throw new Error("Dispatch context cannot be empty.");
  }
  return { text, description };
}

function dispatchSessionName(name: string): string {
  return `dispatch-${name}`.slice(0, 80);
}

function activeWorkspaceView(canonicalWorkspace: string): string {
  const candidates = (vscode.workspace.workspaceFolders ?? []).map(
    ({ uri }) => uri.fsPath
  );
  if (vscode.workspace.workspaceFile?.scheme === "file") {
    candidates.push(dirname(vscode.workspace.workspaceFile.fsPath));
  }
  for (const candidate of candidates) {
    const parts = relative(canonicalWorkspace, candidate).split(sep);
    if (parts[0] === ".wt" && parts[1]) {
      return join(canonicalWorkspace, ".wt", parts[1]);
    }
  }
  return canonicalWorkspace;
}

function isLocal(host: TtHost, registryHost: string): boolean {
  return host.hostname === "localhost" || registryHost === "localhost";
}
