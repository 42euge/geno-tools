import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

test("recognizes only tmux absence diagnostics", async () => {
  const state = processState();
  const module = await loadTtCli(state);

  for (const message of [
    "no server running on /private/tmp/tmux-503/default",
    "no sessions",
    "can't find session: old-work"
  ]) {
    assert.equal(
      module.isTmuxSessionAbsentError(
        new module.TtCommandError(message, ["kill-session"])
      ),
      true
    );
  }
  for (const message of [
    "ssh: connect to host build: Operation timed out",
    "bash: tmux: command not found",
    "permission denied",
    "session not found"
  ]) {
    assert.equal(
      module.isTmuxSessionAbsentError(
        new module.TtCommandError(message, ["kill-session"])
      ),
      false
    );
  }
});

test("kill returns killed or alreadyAbsent without hiding real failures", async () => {
  const state = processState([
    { code: 0 },
    { code: 1, stderr: "no server running on /private/tmp/tmux-503/default\n" },
    { code: 1, stderr: "ssh: connect to host build: Operation timed out\n" }
  ]);
  const { TtCli } = await loadTtCli(state);
  const cli = new TtCli(output());
  const local = { alias: "local", hostname: "localhost", isDefault: true };
  const remote = {
    alias: "build",
    hostname: "build.example.com",
    isDefault: false
  };

  assert.equal(
    await cli.killTmuxSession(local, "localhost", "finished"),
    "killed"
  );
  assert.equal(
    await cli.killTmuxSession(local, "localhost", "already-gone"),
    "alreadyAbsent"
  );
  await assert.rejects(
    cli.killTmuxSession(remote, "build.example.com", "unknown"),
    /Operation timed out/
  );
  assert.deepEqual(JSON.parse(JSON.stringify(state.spawnCalls)), [
    {
      executable: "tmux",
      args: ["kill-session", "-t", "finished"]
    },
    {
      executable: "tmux",
      args: ["kill-session", "-t", "already-gone"]
    },
    {
      executable: "ssh",
      args: [
        "build.example.com",
        "tmux kill-session -t unknown"
      ]
    }
  ]);
});

test("scanRegistry refreshes quietly before reading live state", async () => {
  const registry = {
    schema_version: 1,
    host: "localhost",
    generated_at: "2026-09-03T12:00:00Z",
    workspaces: []
  };
  const state = processState([
    { code: 0 },
    { code: 0, stdout: JSON.stringify(registry) }
  ]);
  const { TtCli } = await loadTtCli(state);
  const cli = new TtCli(output());

  const scanned = await cli.scanRegistry({
      alias: "local",
      hostname: "localhost",
      isDefault: true
    });
  assert.deepEqual(JSON.parse(JSON.stringify(scanned)), registry);
  assert.deepEqual(JSON.parse(JSON.stringify(state.spawnCalls)), [
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "refresh"]
    },
    {
      executable: "tt-test",
      args: ["-H", "local", "registry", "show"]
    }
  ]);
  assert.equal(state.progressCalls, 0);
});

interface SpawnResult {
  code: number;
  stdout?: string;
  stderr?: string;
}

interface ProcessState {
  progressCalls: number;
  spawnCalls: Array<{ executable: string; args: string[] }>;
  spawnResults: SpawnResult[];
}

function processState(spawnResults: SpawnResult[] = []): ProcessState {
  return { progressCalls: 0, spawnCalls: [], spawnResults: [...spawnResults] };
}

function output(): {
  append(): void;
  appendLine(): void;
  show(): void;
} {
  return { append() {}, appendLine() {}, show() {} };
}

interface TtCliModule {
  TtCli: new (output: ReturnType<typeof output>) => {
    killTmuxSession(
      host: { alias: string; hostname: string; isDefault: boolean },
      registryHost: string,
      sessionName: string
    ): Promise<string>;
    scanRegistry(host: {
      alias: string;
      hostname: string;
      isDefault: boolean;
    }): Promise<unknown>;
  };
  TtCommandError: new (
    message: string,
    args: readonly string[],
    exitCode?: number
  ) => Error;
  isTmuxSessionAbsentError(error: unknown): boolean;
}

async function loadTtCli(state: ProcessState): Promise<TtCliModule> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "ttCli.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    plugins: [
      {
        name: "vscode-stub",
        setup(build) {
          build.onResolve({ filter: /^vscode$/ }, () => ({
            path: "vscode",
            namespace: "vscode-stub"
          }));
          build.onLoad({ filter: /.*/, namespace: "vscode-stub" }, () => ({
            contents: `
              const state = globalThis.__processState;
              module.exports = {
                ProgressLocation: { Notification: 15 },
                workspace: {
                  getConfiguration: () => ({
                    get: (key, fallback) => key === "ttPath" ? "tt-test" : fallback
                  })
                },
                window: {
                  withProgress: async (_options, task) => {
                    state.progressCalls += 1;
                    return task({}, {
                      onCancellationRequested: () => ({ dispose() {} })
                    });
                  }
                }
              };
            `,
            loader: "js"
          }));
        }
      },
      {
        name: "child-process-stub",
        setup(build) {
          build.onResolve({ filter: /^node:child_process$/ }, () => ({
            path: "node:child_process",
            namespace: "child-process-stub"
          }));
          build.onLoad({ filter: /.*/, namespace: "child-process-stub" }, () => ({
            contents: `
              const state = globalThis.__processState;
              function stream() {
                const dataListeners = [];
                return {
                  dataListeners,
                  on(event, callback) {
                    if (event === "data") dataListeners.push(callback);
                    return this;
                  }
                };
              }
              function spawn(executable, args) {
                state.spawnCalls.push({ executable, args });
                const result = state.spawnResults.shift() ?? { code: 0 };
                const stdout = stream();
                const stderr = stream();
                const child = {
                  stdout,
                  stderr,
                  kill() {},
                  on(event, callback) {
                    if (event === "close") {
                      Promise.resolve().then(() => {
                        if (result.stdout) {
                          for (const listener of stdout.dataListeners) {
                            listener(Buffer.from(result.stdout));
                          }
                        }
                        if (result.stderr) {
                          for (const listener of stderr.dataListeners) {
                            listener(Buffer.from(result.stderr));
                          }
                        }
                        callback(result.code);
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
      }
    ]
  });

  const compiledModule: { exports: Record<string, unknown> } = { exports: {} };
  vm.runInNewContext(result.outputFiles[0].text, {
    module: compiledModule,
    exports: compiledModule.exports,
    require: createRequire(__filename),
    process,
    Buffer,
    console,
    setTimeout,
    clearTimeout,
    __processState: state
  });
  return compiledModule.exports as unknown as TtCliModule;
}
