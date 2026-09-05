import assert from "node:assert/strict";
import test from "node:test";

import {
  TerminalRegistry,
  TerminalRegistryStorage
} from "../terminalRegistry";

interface TestTerminal {
  name: string;
  creationOptions: { name?: string };
  processId: Promise<number | undefined>;
}

class MemoryStorage implements TerminalRegistryStorage {
  private readonly values = new Map<string, unknown>();

  get<T>(key: string, fallback: T): T {
    return (this.values.get(key) as T | undefined) ?? fallback;
  }

  async update(key: string, value: unknown): Promise<void> {
    this.values.set(key, value);
  }
}

test("restored generic shell names remain eligible for bulk AI naming", () => {
  const registry = new TerminalRegistry();
  const restored = terminal("zsh", 101, "zsh");
  const custom = terminal("database console", 102, "database console");

  registry.observe(restored);
  registry.observe(custom);

  assert.equal(registry.stateFor(restored).naming, "default");
  assert.equal(registry.canBulkName(restored), true);
  assert.equal(registry.stateFor(custom).naming, "manual");
  assert.equal(registry.canBulkName(custom), false);
});

test("AI naming and later manual renames have distinct provenance", async () => {
  const storage = new MemoryStorage();
  const registry = new TerminalRegistry(storage);
  const candidate = terminal("zsh", 201);

  registry.observe(candidate);
  candidate.name = "iterative ui design";
  await registry.recordAiName(candidate, candidate.name);
  assert.equal(registry.stateFor(candidate).naming, "ai");

  candidate.name = "my terminal";
  assert.equal(registry.stateFor(candidate).naming, "manual");
  assert.equal(registry.canBulkName(candidate), false);
});

test("TT origin state survives an extension registry reload", async () => {
  const storage = new MemoryStorage();
  const original = terminal("iterative ui design", 301);
  const first = new TerminalRegistry(storage);
  first.observe(original);
  await first.recordTtLink(original, {
    role: "origin",
    hostAlias: "local",
    sessionName: "iterative-ui-design",
    agent: "codex",
    agentSessionId: "session-123"
  });

  const restored = terminal("iterative ui design", 301);
  const second = new TerminalRegistry(storage);
  await second.restore([restored]);

  assert.deepEqual(second.stateFor(restored).tt, {
    role: "origin",
    hostAlias: "local",
    sessionName: "iterative-ui-design",
    agent: "codex",
    agentSessionId: "session-123"
  });
  assert.equal(second.canBulkName(restored), false);
});

function terminal(
  name: string,
  processId: number,
  creationName?: string
): TestTerminal {
  return {
    name,
    creationOptions: creationName === undefined ? {} : { name: creationName },
    processId: Promise.resolve(processId)
  };
}
