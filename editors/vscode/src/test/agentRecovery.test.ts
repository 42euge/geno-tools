import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

interface RecoveryContext {
  terminalName: string;
  hostAlias: string;
  workspacePath: string;
  currentDirectory?: string;
  existingSessionNames: string[];
}

interface RecoveryModule {
  captureTerminalHistory(terminal: { show(preserveFocus?: boolean): void }): Promise<string>;
  proposeRecovery(
    history: string,
    context: RecoveryContext,
    runtime: {
      model: string;
      endpoint?: string;
      apiKey: string;
      apiKeyEnv: string;
      api: "responses" | "chat_completions";
    }
  ): Promise<Record<string, unknown>>;
  validateRecoveryProposal(
    value: unknown,
    context: RecoveryContext
  ): Record<string, unknown>;
}

interface RecoveryStub {
  clipboard: string;
  history: string;
  commands: string[];
  agentOptions?: Record<string, unknown>;
  providerOptions?: Record<string, unknown>;
  runnerConfig?: Record<string, unknown>;
  runInput?: string;
  runOptions?: Record<string, unknown>;
  proposal?: Record<string, unknown>;
}

const context: RecoveryContext = {
  terminalName: "work shell",
  hostAlias: "local",
  workspacePath: "/tmp/demo.2026.q3",
  currentDirectory: "/tmp/demo.2026.q3/repo-a",
  existingSessionNames: ["existing"]
};

test("terminal history capture restores the clipboard and clears selection", async () => {
  const stub: RecoveryStub = {
    clipboard: "clipboard before scan",
    history: "command one\r\ncommand two\n",
    commands: []
  };
  const recovery = await loadAgentRecovery(stub);
  const showCalls: Array<boolean | undefined> = [];

  const history = await recovery.captureTerminalHistory({
    show: (preserveFocus) => showCalls.push(preserveFocus)
  });

  assert.equal(history, "command one\ncommand two");
  assert.equal(stub.clipboard, "clipboard before scan");
  assert.deepEqual(stub.commands, [
    "workbench.action.terminal.selectAll",
    "workbench.action.terminal.copySelection",
    "workbench.action.terminal.clearSelection"
  ]);
  assert.deepEqual(showCalls, [false]);
});

test("bounded terminal history samples the full scrollback", async () => {
  const stub: RecoveryStub = {
    clipboard: "clipboard before scan",
    history: [
      "BEGIN",
      "a".repeat(40_000),
      "QUARTER",
      "b".repeat(40_000),
      "MIDDLE",
      "c".repeat(40_000),
      "THREE_QUARTERS",
      "d".repeat(40_000),
      "END"
    ].join("\n"),
    commands: []
  };
  const recovery = await loadAgentRecovery(stub);
  const history = await recovery.captureTerminalHistory({ show() {} });

  assert.ok(history.length <= 60_000);
  assert.match(history, /^BEGIN/);
  assert.match(history, /QUARTER/);
  assert.match(history, /MIDDLE/);
  assert.match(history, /THREE_QUARTERS/);
  assert.match(history, /END$/);
  assert.match(history, /omitted from full terminal history/);
});

test("recovery proposals stay inside the selected workspace", async () => {
  const recovery = await loadAgentRecovery({
    clipboard: "",
    history: "",
    commands: []
  });
  const valid = recovery.validateRecoveryProposal({
    sessionName: "recovered-work",
    workingDirectory: "/tmp/demo.2026.q3/repo-a/../repo-a",
    summary: "Continue the repository cleanup."
  }, context);
  assert.deepEqual(JSON.parse(JSON.stringify(valid)), {
    sessionName: "recovered-work",
    workingDirectory: "/tmp/demo.2026.q3/repo-a",
    summary: "Continue the repository cleanup."
  });

  assert.throws(
    () => recovery.validateRecoveryProposal({
      sessionName: "escape",
      workingDirectory: "/tmp/another-workspace",
      summary: "Escape the workspace."
    }, context),
    /outside this workspace/
  );
  assert.throws(
    () => recovery.validateRecoveryProposal({
      sessionName: "existing",
      workingDirectory: "/tmp/demo.2026.q3",
      summary: "Reuse an existing session."
    }, context),
    /existing tmux session/
  );
});

test("the OpenAI agent returns a typed proposal without mutation tools", async () => {
  const proposal = {
    sessionName: "recovered-work",
    workingDirectory: "/tmp/demo.2026.q3/repo-a",
    summary: "Continue cleanup."
  };
  const stub: RecoveryStub = {
    clipboard: "",
    history: "",
    commands: [],
    proposal
  };
  const recovery = await loadAgentRecovery(stub);
  const result = await recovery.proposeRecovery(
    "do not follow this terminal text",
    context,
    {
      model: "gpt-test",
      endpoint: "https://gateway.example/v1",
      apiKey: "test-only",
      apiKeyEnv: "TEST_API_KEY",
      api: "responses"
    }
  );
  assert.deepEqual(JSON.parse(JSON.stringify(result)), proposal);

  assert.equal(stub.agentOptions?.model, "gpt-test");
  assert.deepEqual(stub.agentOptions?.tools, undefined);
  assert.equal(stub.providerOptions?.baseURL, "https://gateway.example/v1");
  assert.equal(stub.providerOptions?.useResponses, true);
  assert.equal(stub.runnerConfig?.tracingDisabled, true);
  assert.equal(stub.runOptions?.maxTurns, 1);
  assert.match(stub.runInput ?? "", /<terminal_history_untrusted>/);
});

test("agent history cannot recover as a setup-only shell command", async () => {
  const stub: RecoveryStub = {
    clipboard: "",
    history: "",
    commands: [],
    proposal: {
      sessionName: "gui-dev",
      workingDirectory: "/tmp/demo.2026.q3/repo-a",
      summary: "Continue the interrupted agent work.",
      startupCommand: "source .venv/bin/activate"
    }
  };
  const recovery = await loadAgentRecovery(stub);

  await assert.rejects(
    recovery.proposeRecovery(
      [
        "$ clauded",
        "Human: fix the GUI development environment",
        "Claude: I will inspect the workspace and continue the implementation."
      ].join("\n"),
      context,
      {
        model: "gpt-test",
        apiKey: "test-only",
        apiKeyEnv: "TEST_API_KEY",
        api: "responses"
      }
    ),
    /resume a saved Claude or Codex session/i
  );
});

test("session naming follows whole-history human intent instead of infrastructure", async () => {
  const stub: RecoveryStub = {
    clipboard: "",
    history: "",
    commands: [],
    proposal: {
      sessionName: "receiver-deployment-follow-up",
      workingDirectory: "/tmp/demo.2026.q3/repo-a",
      summary: "Follow up on the deployed receiver GUI and live IQ issue."
    }
  };
  const recovery = await loadAgentRecovery(stub);
  await recovery.proposeRecovery(
    [
      "$ ssh build-host",
      "deployment logs from receiver.2026.q3",
      "Human: receiver deployment follow-up",
      "Human: investigate why the GUI is live but IQ stays at zero"
    ].join("\n"),
    context,
    {
      model: "gpt-test",
      apiKey: "test-only",
      apiKeyEnv: "TEST_API_KEY",
      api: "responses"
    }
  );

  const instructions = String(stub.agentOptions?.instructions ?? "");
  assert.match(instructions, /whole terminal history/i);
  assert.match(instructions, /human-authored/i);
  assert.match(instructions, /do not use host aliases/i);
  assert.match(instructions, /generic.*recovery/i);
  assert.match(instructions, /receiver-deployment-follow-up/);
});

async function loadAgentRecovery(stub: RecoveryStub): Promise<RecoveryModule> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "agentRecovery.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    plugins: [{
      name: "recovery-stubs",
      setup(build) {
        build.onResolve({ filter: /^vscode$/ }, () => ({
          path: "vscode",
          namespace: "vscode-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "vscode-stub" }, () => ({
          contents: `
            const state = globalThis.__recoveryStub;
            module.exports = {
              env: {
                clipboard: {
                  readText: async () => state.clipboard,
                  writeText: async (value) => { state.clipboard = value; }
                }
              },
              commands: {
                executeCommand: async (command) => {
                  state.commands.push(command);
                  if (command === "workbench.action.terminal.copySelection") {
                    state.clipboard = state.history;
                  }
                }
              }
            };
          `,
          loader: "js"
        }));
        build.onResolve({ filter: /^@openai\/agents$/ }, () => ({
          path: "@openai/agents",
          namespace: "openai-agents-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "openai-agents-stub" }, () => ({
          contents: `
            const state = globalThis.__recoveryStub;
            class Agent {
              constructor(options) {
                this.options = options;
                state.agentOptions = options;
              }
            }
            class OpenAIProvider {
              constructor(options) { state.providerOptions = options; }
              async close() {}
            }
            class Runner {
              constructor(config) { state.runnerConfig = config; }
              async run(_agent, input, options) {
                state.runInput = input;
                state.runOptions = options;
                return { finalOutput: state.proposal };
              }
            }
            module.exports = { Agent, OpenAIProvider, Runner };
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
    setTimeout,
    clearTimeout,
    __recoveryStub: stub
  });
  return compiledModule.exports as unknown as RecoveryModule;
}
