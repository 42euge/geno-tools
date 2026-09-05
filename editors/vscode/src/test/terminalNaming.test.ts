import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import test from "node:test";
import vm from "node:vm";

import * as esbuild from "esbuild";

interface NamingContext {
  terminalName: string;
  workingDirectory?: string;
  existingNames: string[];
}

interface NamingModule {
  proposeTerminalName(
    history: string,
    context: NamingContext,
    runtime: {
      model: string;
      endpoint?: string;
      apiKey: string;
      apiKeyEnv: string;
      api: "responses" | "chat_completions";
    }
  ): Promise<{ tag: string }>;
  validateTerminalNameProposal(
    value: unknown,
    context: NamingContext
  ): { tag: string };
}

interface NamingStub {
  agentOptions?: Record<string, unknown>;
  providerOptions?: Record<string, unknown>;
  proposal?: Record<string, unknown>;
  runInput?: string;
  runOptions?: Record<string, unknown>;
  runnerConfig?: Record<string, unknown>;
}

const context: NamingContext = {
  terminalName: "codex",
  workingDirectory: "/tmp/demo.2026.q3",
  existingNames: ["release notes"]
};

test("terminal tags are normalized, short, and unique", async () => {
  const naming = await loadTerminalNaming({});

  assert.deepEqual(
    plain(naming.validateTerminalNameProposal(
      { tag: "  Receiver   Debug " },
      context
    )),
    { tag: "receiver debug" }
  );
  assert.throws(
    () => naming.validateTerminalNameProposal(
      { tag: "this tag has four words" },
      context
    ),
    /one to three words/i
  );
  assert.throws(
    () => naming.validateTerminalNameProposal({ tag: "release notes" }, context),
    /already in use/i
  );
  assert.throws(
    () => naming.validateTerminalNameProposal(
      { tag: "debug\u202e codex" },
      context
    ),
    /letters and numbers/i
  );
});

test("the naming agent returns a typed tag without mutation tools", async () => {
  const stub: NamingStub = { proposal: { tag: "session cleanup" } };
  const naming = await loadTerminalNaming(stub);

  const result = await naming.proposeTerminalName(
    "Human: finish the session cleanup",
    context,
    {
      model: "gpt-test",
      endpoint: "https://gateway.example/v1",
      apiKey: "test-only",
      apiKeyEnv: "TEST_API_KEY",
      api: "responses"
    }
  );

  assert.deepEqual(plain(result), { tag: "session cleanup" });
  assert.equal(stub.agentOptions?.model, "gpt-test");
  assert.equal(stub.agentOptions?.tools, undefined);
  assert.ok(stub.agentOptions?.outputType);
  assert.match(String(stub.agentOptions?.instructions ?? ""), /one to three/i);
  assert.match(stub.runInput ?? "", /<terminal_history_untrusted>/);
  assert.equal(stub.providerOptions?.baseURL, "https://gateway.example/v1");
  assert.equal(stub.providerOptions?.useResponses, true);
  assert.equal(stub.runnerConfig?.tracingDisabled, true);
  assert.equal(stub.runOptions?.maxTurns, 1);
});

test("the naming agent receives corroborated active feature evidence", async () => {
  const stub: NamingStub = { proposal: { tag: "iterative ui design" } };
  const naming = await loadTerminalNaming(stub);
  const history = [
    "Human: Are there pull requests or uncommitted work?",
    "Assistant: Uncommitted work is on feat/iterative-ui-design:",
    "- project/docs/acceptance/iterative-ui-design.md",
    "The eval-engine worktree is clean."
  ].join("\n");

  await naming.proposeTerminalName(history, context, {
    model: "gpt-test",
    endpoint: "https://gateway.example/v1",
    apiKey: "test-only",
    apiKeyEnv: "TEST_API_KEY",
    api: "responses"
  });

  const inputContext = JSON.parse(
    (stub.runInput ?? "")
      .split("Terminal context:\n")[1]
      ?.split("\n<terminal_history_untrusted>")[0] ?? "null"
  ) as { taskEvidence?: unknown };
  assert.deepEqual(inputContext.taskEvidence, [
    {
      label: "iterative ui design",
      mentions: 2,
      sources: ["branch", "acceptance file"]
    }
  ]);
});

function plain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

async function loadTerminalNaming(stub: NamingStub): Promise<NamingModule> {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, "..", "terminalNaming.ts")],
    bundle: true,
    format: "cjs",
    platform: "node",
    write: false,
    plugins: [{
      name: "naming-stubs",
      setup(build) {
        build.onResolve({ filter: /^@openai\/agents$/ }, () => ({
          path: "@openai/agents",
          namespace: "openai-agents-stub"
        }));
        build.onLoad({ filter: /.*/, namespace: "openai-agents-stub" }, () => ({
          contents: `
            const state = globalThis.__namingStub;
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
    __namingStub: stub
  });
  return compiledModule.exports as unknown as NamingModule;
}
