import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { isAbsolute, resolve } from "node:path";

import { parse } from "yaml";

export type AgentApi = "responses" | "chat_completions";

export interface AgentRuntimeConfig {
  model: string;
  endpoint?: string;
  apiKey: string;
  apiKeyEnv: string;
  api: AgentApi;
  configPath?: string;
}

export interface AgentConfigOptions {
  configPath?: string;
  modelOverride?: string;
  environment?: NodeJS.ProcessEnv;
}

interface GenoConfig {
  llm?: {
    endpoint?: unknown;
    model?: unknown;
    api_key_env?: unknown;
    api?: unknown;
  };
}

const DEFAULT_CONFIG_PATH = "~/.geno/config.yaml";
const ENV_NAME = /^[A-Za-z_][A-Za-z0-9_]*$/;

export async function loadAgentRuntimeConfig(
  options: AgentConfigOptions = {}
): Promise<AgentRuntimeConfig> {
  const environment = options.environment ?? process.env;
  const configPath = expandConfigPath(options.configPath ?? DEFAULT_CONFIG_PATH);
  const config = await readGenoConfig(configPath);
  const llm = config?.llm ?? {};

  const model = firstNonEmpty(
    options.modelOverride,
    stringValue(llm.model),
    environment.OPENAI_DEFAULT_MODEL,
    "gpt-5.6"
  );
  const endpoint = firstNonEmpty(
    stringValue(llm.endpoint),
    environment.OPENAI_BASE_URL
  );
  if (endpoint) {
    validateEndpoint(endpoint, configPath);
  }

  const apiKeyEnv = firstNonEmpty(
    stringValue(llm.api_key_env),
    "OPENAI_API_KEY"
  );
  if (!ENV_NAME.test(apiKeyEnv)) {
    throw new Error(
      `Invalid llm.api_key_env in ${configPath}: ${apiKeyEnv}`
    );
  }
  const apiKey = environment[apiKeyEnv]?.trim();
  if (!apiKey) {
    throw new Error(
      `${apiKeyEnv} is not available to the VS Code extension host. Set it before launching VS Code.`
    );
  }

  const api = parseApi(stringValue(llm.api), configPath);
  return {
    model,
    endpoint,
    apiKey,
    apiKeyEnv,
    api,
    configPath: config ? configPath : undefined
  };
}

async function readGenoConfig(path: string): Promise<GenoConfig | undefined> {
  let source: string;
  try {
    source = await readFile(path, "utf8");
  } catch (error) {
    if (isNodeError(error) && error.code === "ENOENT") {
      return undefined;
    }
    throw new Error(`Unable to read Geno agent config ${path}: ${messageOf(error)}`);
  }

  try {
    const value: unknown = parse(source);
    if (value === undefined || value === null) {
      return {};
    }
    if (typeof value !== "object" || Array.isArray(value)) {
      throw new Error("the YAML root must be an object");
    }
    return value as GenoConfig;
  } catch (error) {
    throw new Error(`Invalid Geno agent config ${path}: ${messageOf(error)}`);
  }
}

function expandConfigPath(path: string): string {
  const expanded = path === "~"
    ? homedir()
    : path.startsWith("~/")
      ? resolve(homedir(), path.slice(2))
      : path;
  if (!isAbsolute(expanded)) {
    throw new Error(`Geno agent config path must be absolute: ${path}`);
  }
  return expanded;
}

function parseApi(value: string | undefined, configPath: string): AgentApi {
  const api = value || "responses";
  if (api === "responses" || api === "chat_completions") {
    return api;
  }
  throw new Error(
    `Invalid llm.api in ${configPath}: use responses or chat_completions.`
  );
}

function validateEndpoint(endpoint: string, configPath: string): void {
  let parsed: URL;
  try {
    parsed = new URL(endpoint);
  } catch {
    throw new Error(`Invalid llm.endpoint URL in ${configPath}: ${endpoint}`);
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    throw new Error(
      `Invalid llm.endpoint protocol in ${configPath}: ${parsed.protocol}`
    );
  }
}

function firstNonEmpty(
  ...values: Array<string | undefined>
): string {
  return values.find((value) => value?.trim())?.trim() ?? "";
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return typeof error === "object" && error !== null && "code" in error;
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
