import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

interface SpawnCall {
  executable: string;
  args: string[];
  cwd?: string;
  input?: string;
}

interface VscodeStub {
  commands: Map<string, (...args: unknown[]) => Promise<unknown>>;
  errors: string[];
  editorText: string;
  inputValues: string[];
  quickPickTitles?: string[];
  spawnCalls: SpawnCall[];
  warningValues: Array<string | undefined>;
  workspaceFolders: string[];
}

test("dispatch control sends the active document to tt over stdin", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errors: [],
    editorText: "# Parser handoff\n\nImplement and verify the parser fix.\n",
    inputValues: ["parser-fix"],
    spawnCalls: [],
    warningValues: ["Dispatch"],
    workspaceFolders: ["/tmp/parser.2026.q3/.wt/feature/parser"]
  };
  const extension = await loadExtension(stub);
  extension.activate({ subscriptions: [] });
  const command = stub.commands.get("genoTools.dispatchWorkspace");
  assert.ok(command, "dispatch command should be registered");

  await command(localWorkspaceNode());

  assert.deepEqual(stub.errors, []);
  assert.ok(
    stub.spawnCalls.some(({ executable, args }) =>
      executable === "tt-test" && args.length === 1 && args[0] === "hosts"
    )
  );
  const dispatchCall = stub.spawnCalls.find(
    ({ args }) => args[0] === "dispatch" && args[1] !== "list"
  );
  assert.ok(dispatchCall);
  assert.equal(dispatchCall.executable, "tt-test");
  assert.deepEqual(Array.from(dispatchCall.args), [
    "dispatch",
    "build",
    "--name",
    "parser-fix",
    "--workspace",
    "/tmp/parser.2026.q3/.wt/feature",
    "--context-file",
    "-"
  ]);
  assert.equal(dispatchCall.cwd, "/tmp/parser.2026.q3/.wt/feature");
  assert.equal(dispatchCall.input, stub.editorText);
});

test("dispatching a mirror reuses its host instead of asking again", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errors: [],
    editorText: "# Build on the mirror\n",
    inputValues: ["parser-fix"],
    quickPickTitles: [],
    spawnCalls: [],
    warningValues: ["Dispatch"],
    workspaceFolders: ["/tmp/parser.2026.q3"]
  };
  const extension = await loadExtension(stub);
  extension.activate({ subscriptions: [] });
  const command = stub.commands.get("genoTools.dispatchMirror");
  assert.ok(command, "dispatch mirror command should be registered");
  const source = localWorkspaceNode();
  const mirror = {
    ...localWorkspaceNode(),
    host: { alias: "build", hostname: "build.example.com", isDefault: false },
    registry: {
      schema_version: 1,
      host: "build.example.com",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    }
  };

  await command({ kind: "remoteMirror", source, mirror });

  assert.ok(!stub.quickPickTitles?.some((title) => title.startsWith("Dispatch parser")));
  assert.ok(stub.quickPickTitles?.includes("Dispatch Context"));
  const dispatchCall = stub.spawnCalls.find(
    ({ args }) => args[0] === "dispatch" && args[1] !== "list"
  );
  assert.equal(dispatchCall?.args[1], "build");
});

test("mirror control only asks for a host before mirroring", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errors: [],
    editorText: "",
    inputValues: [],
    spawnCalls: [],
    warningValues: [],
    workspaceFolders: []
  };
  const extension = await loadExtension(stub);
  extension.activate({ subscriptions: [] });
  const command = stub.commands.get("genoTools.mirrorWorkspace");
  assert.ok(command, "mirror command should be registered");

  await command(localWorkspaceNode());

  assert.deepEqual(stub.errors, []);
  assert.equal(stub.warningValues.length, 0, "mirror should not ask for confirmation");
  assert.ok(
    stub.spawnCalls.some(({ executable, args }) =>
      executable === "tt-test" &&
      Array.from(args).join(" ") ===
        "-H local mirror chore.geno.parser.2026.q3 build"
    )
  );
});

test("manifest makes mirror primary and dispatch an action on a mirror", () => {
  const manifest = JSON.parse(
    readFileSync(join(__dirname, "..", "..", "package.json"), "utf8")
  ) as {
    contributes: {
      views: {
        genoTools: Array<{ id: string; when?: string }>;
      };
      commands: Array<{ command: string }>;
      menus: {
        "view/title": Array<{ command: string; group: string }>;
        "view/item/context": Array<{ command: string; group: string }>;
      };
    };
  };
  const commands = manifest.contributes.commands.map(({ command }) => command);
  assert.ok(commands.includes("genoTools.dispatchWorkspace"));
  assert.ok(commands.includes("genoTools.dispatchMirror"));
  assert.ok(commands.includes("genoTools.manageDispatches"));
  assert.ok(
    manifest.contributes.views.genoTools.some(
      ({ id, when }) =>
        id === "genoTools.remoteMirrors" &&
        when === "genoTools.hasCurrentWorkspaceMirror"
    )
  );
  assert.ok(
    manifest.contributes.menus["view/item/context"].some(
      ({ command, group }) =>
        command === "genoTools.dispatchWorkspace" && group === "remote@2"
    )
  );
  assert.ok(
    manifest.contributes.menus["view/title"].some(
      ({ command, group }) =>
        command === "genoTools.mirrorWorkspace" && group === "navigation@3"
    )
  );
  assert.ok(
    manifest.contributes.menus["view/item/context"].some(
      ({ command, group }) =>
        command === "genoTools.dispatchMirror" && group === "inline@1"
    )
  );
});

test("dispatch manager confirms stop and invokes safe recall", async () => {
  const stub: VscodeStub = {
    commands: new Map(),
    errors: [],
    editorText: "",
    inputValues: [],
    spawnCalls: [],
    warningValues: ["Stop and Recall"],
    workspaceFolders: []
  };
  const extension = await loadExtension(stub);
  extension.activate({ subscriptions: [] });
  const command = stub.commands.get("genoTools.manageDispatches");
  assert.ok(command, "manage dispatches command should be registered");

  await command();

  assert.deepEqual(stub.errors, []);
  assert.deepEqual(
    stub.spawnCalls.map(({ args }) => Array.from(args)),
    [
      ["dispatch", "list", "--json"],
      ["recall", "parser-fix", "--stop"],
      ["dispatch", "list", "--json"]
    ]
  );
});

function localWorkspaceNode(): object {
  return {
    kind: "workspace",
    host: { alias: "local", hostname: "localhost", isDefault: true },
    registry: {
      schema_version: 1,
      host: "localhost",
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: []
    },
    workspace: {
      id: "chore.geno.parser.2026.q3",
      track: "chore",
      domain: "geno",
      name: "parser",
      born: "2026.q3",
      path: "/tmp/parser.2026.q3",
      repos: [],
      state: { tmux: { sessions: [] } }
    }
  };
}

async function loadExtension(
  stub: VscodeStub
): Promise<{ activate(context: { subscriptions: unknown[] }): void }> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "extension.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    external: ["@openai/agents", "yaml", "zod"],
    plugins: [{
      name: "vscode-stub",
      setup(build) {
        build.onResolve({ filter: /^vscode$/ }, () => ({
          path: "vscode",
          namespace: "stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "stub" }, () => ({
          contents: `
            const state = globalThis.__vscodeStub;
            class EventEmitter {
              event = () => ({ dispose() {} });
              fire() {}
              dispose() {}
            }
            class TreeItem { constructor(label, collapsibleState) { this.label = label; this.collapsibleState = collapsibleState; } }
            class MarkdownString { constructor(value) { this.value = value; } }
            class ThemeIcon { constructor(id) { this.id = id; } }
            module.exports = {
              EventEmitter,
              TreeItem,
              MarkdownString,
              ThemeIcon,
              TreeItemCollapsibleState: { None: 0, Collapsed: 1, Expanded: 2 },
              ProgressLocation: { Notification: 15 },
              workspace: {
                workspaceFolders: state.workspaceFolders.map((path) => ({ uri: { scheme: "file", fsPath: path, path } })),
                workspaceFile: undefined,
                fs: { readFile: async () => new Uint8Array() },
                onDidChangeWorkspaceFolders: () => ({ dispose() {} }),
                getConfiguration: () => ({ get: (key, fallback) => key === "ttPath" ? "tt-test" : fallback }),
                openTextDocument: async (uri) => ({ uri })
              },
              Uri: { file: (path) => ({ scheme: "file", path, fsPath: path }), from: (parts) => parts },
              window: {
                terminals: [],
                onDidOpenTerminal: () => ({ dispose() {} }),
                onDidCloseTerminal: () => ({ dispose() {} }),
                onDidChangeTerminalShellIntegration: () => ({ dispose() {} }),
                activeTextEditor: {
                  selection: { isEmpty: true },
                  document: { fileName: "/tmp/HANDOFF.md", getText: () => state.editorText }
                },
                createOutputChannel: () => ({ append() {}, appendLine() {}, show() {}, dispose() {} }),
                createTreeView: () => ({ selection: [], dispose() {} }),
                withProgress: async (_options, task) => task({}, { onCancellationRequested: () => ({ dispose() {} }) }),
                createTerminal: () => ({ show() {}, sendText() {} }),
                showInputBox: async () => state.inputValues.shift(),
                showQuickPick: async (items, options) => {
                  state.quickPickTitles?.push(options?.title ?? "");
                  if (options?.title?.startsWith("Dispatch parser")) return items.find((item) => item.label === "build");
                  if (options?.title?.startsWith("Mirror parser")) return items.find((item) => item.label === "build");
                  if (options?.title === "Dispatch Context") return items.find((item) => item.label === "Use Active Document");
                  if (options?.title === "Manage Remote Dispatches") return items[0];
                  if (options?.title === "parser-fix") return items.find((item) => item.label === "Stop and Recall");
                  return undefined;
                },
                showWarningMessage: async () => state.warningValues.shift(),
                showInformationMessage: async () => undefined,
                showErrorMessage: async (message) => { state.errors.push(message); return undefined; },
                showOpenDialog: async () => undefined,
                showTextDocument: async () => undefined
              },
              commands: {
                registerCommand: (name, callback) => { state.commands.set(name, callback); return { dispose() {} }; },
                executeCommand: async () => undefined
              },
              env: { clipboard: { writeText: async () => undefined } }
            };
          `,
          loader: "js"
        }));
        build.onResolve({ filter: /^node:child_process$/ }, () => ({
          path: "node:child_process",
          namespace: "child-process-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "child-process-stub" }, () => ({
          contents: `
            const state = globalThis.__vscodeStub;
            function spawn(executable, args, options) {
              const call = { executable, args, cwd: options.cwd, input: undefined };
              state.spawnCalls.push(call);
              const stdoutListeners = {};
              const stderrListeners = {};
              const stream = (listeners) => ({ on(event, callback) { listeners[event] = callback; return this; } });
              const child = {
                stdout: stream(stdoutListeners),
                stderr: stream(stderrListeners),
                stdin: { end(input) { call.input = input; } },
                kill() {},
                on(event, callback) {
                  if (event === "close") {
                    Promise.resolve().then(() => {
                      if (args.length === 1 && args[0] === "hosts") {
                        stdoutListeners.data?.(Buffer.from("local -> localhost (default)\\nbuild -> build.example.com\\n"));
                      }
                      if (args.join(" ") === "dispatch list --json") {
                        const recalled = state.spawnCalls.some((call) => call.args[0] === "recall");
                        stdoutListeners.data?.(Buffer.from(JSON.stringify([{
                          name: "parser-fix",
                          status: recalled ? "recalled" : "active",
                          session: "dispatch-parser-fix",
                          created_at: "2026-09-01T12:00:00+00:00",
                          source: { workspace_view: "/tmp/parser.2026.q3" },
                          target: { host_alias: "build", hostname: "build.example.com" },
                          ...(recalled ? { return_file: "/tmp/RETURN.md" } : {})
                        }])));
                      }
                      callback(0);
                    });
                  }
                  return child;
                }
              };
              return child;
            }
            module.exports = { spawn };
          `,
          loader: "js"
        }));
      }
    }]
  });

  const compiledModule: { exports: Record<string, unknown> } = { exports: {} };
  vm.runInNewContext(result.outputFiles[0].text, {
    module: compiledModule,
    exports: compiledModule.exports,
    require: createRequire(__filename),
    process,
    Buffer,
    TextDecoder,
    console,
    setTimeout,
    clearTimeout,
    __vscodeStub: stub
  });
  return compiledModule.exports as unknown as {
    activate(context: { subscriptions: unknown[] }): void;
  };
}
