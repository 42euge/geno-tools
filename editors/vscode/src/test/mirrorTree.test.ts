import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

test("remote mirror tree shows the matching host and enables its view", async () => {
  const contexts: unknown[][] = [];
  const RemoteMirrorTreeProvider = await loadProvider(contexts);
  const source = workspaceNode("local", "localhost", "/tmp/demo.2026.q3");
  const mirror = workspaceNode(
    "build",
    "build.example.com",
    "/home/dev/code/chore/geno/demo.2026.q3"
  );
  const provider = new RemoteMirrorTreeProvider(
    async () => source,
    async () => [mirror]
  );

  const nodes = await provider.getChildren();
  const item = provider.getTreeItem(nodes[0]);

  assert.equal(item.label, "build");
  assert.equal(item.contextValue, "remoteMirror");
  assert.equal(item.command?.command, "genoTools.openWorkspaceInNewWindow");
  assert.equal(item.command?.arguments?.[0], mirror);
  assert.deepEqual(Array.from(contexts.at(-1) ?? []), [
    "setContext",
    "genoTools.hasCurrentWorkspaceMirror",
    true
  ]);
});

function workspaceNode(alias: string, hostname: string, path: string): object {
  const workspace = {
    id: "chore.geno.demo.2026.q3",
    track: "chore",
    domain: "geno",
    name: "demo",
    born: "2026.q3",
    path,
    repos: [{ name: "geno-tools" }, { name: "geno-tt" }],
    state: { tmux: { sessions: [] } }
  };
  return {
    kind: "workspace",
    host: { alias, hostname, isDefault: alias === "local" },
    registry: {
      schema_version: 1,
      host: hostname,
      generated_at: "2026-09-01T00:00:00Z",
      workspaces: [workspace]
    },
    workspace
  };
}

async function loadProvider(
  contexts: unknown[][]
): Promise<new (
  currentWorkspace: () => Promise<object | undefined>,
  mirrorsFor: (source: object) => Promise<object[]>
) => {
  getChildren(): Promise<object[]>;
  getTreeItem(node: object): {
    label: string;
    contextValue?: string;
    command?: { command: string; arguments?: unknown[] };
  };
}> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "mirrorTree.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
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
            class TreeItem {
              constructor(label, collapsibleState) {
                this.label = label;
                this.collapsibleState = collapsibleState;
              }
            }
            class MarkdownString { constructor(value) { this.value = value; } }
            class ThemeIcon { constructor(id) { this.id = id; } }
            module.exports = {
              EventEmitter,
              TreeItem,
              MarkdownString,
              ThemeIcon,
              TreeItemCollapsibleState: { None: 0 },
              commands: {
                executeCommand: async (...args) => { state.contexts.push(args); }
              }
            };
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
    console,
    __vscodeStub: { contexts }
  });
  return compiledModule.exports.RemoteMirrorTreeProvider as never;
}
