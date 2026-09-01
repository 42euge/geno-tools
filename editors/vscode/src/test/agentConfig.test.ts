import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { loadAgentRuntimeConfig } from "../agentConfig";

test("Geno YAML config selects a custom endpoint without storing its token", async () => {
  const directory = await mkdtemp(join(tmpdir(), "geno-agent-config-"));
  const configPath = join(directory, "config.yaml");
  try {
    await writeFile(configPath, [
      "llm:",
      "  endpoint: https://gateway.example/v1",
      "  model: gateway-model",
      "  api_key_env: GATEWAY_API_KEY",
      "  api: responses",
      ""
    ].join("\n"));
    const config = await loadAgentRuntimeConfig({
      configPath,
      environment: { GATEWAY_API_KEY: "secret-from-environment" }
    });

    assert.deepEqual(config, {
      model: "gateway-model",
      endpoint: "https://gateway.example/v1",
      apiKey: "secret-from-environment",
      apiKeyEnv: "GATEWAY_API_KEY",
      api: "responses",
      configPath
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("VS Code model overrides Geno config while endpoint remains shared", async () => {
  const directory = await mkdtemp(join(tmpdir(), "geno-agent-config-"));
  const configPath = join(directory, "config.yaml");
  try {
    await writeFile(configPath, [
      "llm:",
      "  endpoint: https://gateway.example/v1",
      "  model: shared-model",
      ""
    ].join("\n"));
    const config = await loadAgentRuntimeConfig({
      configPath,
      modelOverride: "window-model",
      environment: { OPENAI_API_KEY: "test-only" }
    });

    assert.equal(config.model, "window-model");
    assert.equal(config.endpoint, "https://gateway.example/v1");
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("Geno config reports a missing named credential", async () => {
  const directory = await mkdtemp(join(tmpdir(), "geno-agent-config-"));
  const configPath = join(directory, "config.yaml");
  try {
    await writeFile(configPath, [
      "llm:",
      "  api_key_env: MISSING_GATEWAY_KEY",
      ""
    ].join("\n"));

    await assert.rejects(
      loadAgentRuntimeConfig({ configPath, environment: {} }),
      /MISSING_GATEWAY_KEY is not available/
    );
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
