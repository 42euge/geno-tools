import { spawn } from "node:child_process";
import { dirname, join } from "node:path";

type LayoutQuery = (databasePath: string) => Promise<string>;

/**
 * UNSUPPORTED VSCODE INTERNAL STATE
 *
 * VS Code's extension API intentionally omits native terminal split groups.
 * This adapter reads the workbench's private SQLite state so Geno Tools can
 * mirror the native terminal list. Keep failures non-fatal: the key, schema,
 * database location, or sqlite3 availability may change without notice.
 */
export class UnsupportedVsCodeTerminalLayoutReader {
  private reportedFailure = false;

  constructor(
    private readonly workspaceStoragePath: string | undefined,
    private readonly report: (message: string) => void,
    private readonly query: LayoutQuery = queryInternalLayout
  ) {}

  async readGroups(): Promise<number[][] | undefined> {
    if (!this.workspaceStoragePath) {
      return undefined;
    }
    try {
      const databasePath = join(
        dirname(this.workspaceStoragePath),
        "state.vscdb"
      );
      const value = await this.query(databasePath);
      return parseVsCodeTerminalGroups(value);
    } catch (error) {
      if (!this.reportedFailure) {
        this.reportedFailure = true;
        const message = error instanceof Error ? error.message : String(error);
        this.report(
          `[terminal layout] Unsupported VS Code state unavailable; ` +
          `showing terminals without split markers: ${message}`
        );
      }
      return undefined;
    }
  }
}

export function parseVsCodeTerminalGroups(
  value: string
): number[][] | undefined {
  let layout: unknown;
  try {
    layout = JSON.parse(value);
  } catch {
    return undefined;
  }
  if (!isObject(layout) || !Array.isArray(layout.tabs)) {
    return undefined;
  }
  const groups = layout.tabs.map((tab) => {
    if (!isObject(tab) || !Array.isArray(tab.terminals)) {
      return [];
    }
    return tab.terminals.flatMap((entry) =>
      isObject(entry) &&
      typeof entry.terminal === "number" &&
      Number.isInteger(entry.terminal)
        ? [entry.terminal]
        : []
    );
  });
  return groups.every((group) => group.length > 0) ? groups : undefined;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

const LAYOUT_QUERY =
  "SELECT value FROM ItemTable " +
  "WHERE key = 'terminal.integrated.layoutInfo' LIMIT 1;";

function queryInternalLayout(databasePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "sqlite3",
      ["-readonly", "-noheader", databasePath, LAYOUT_QUERY],
      { stdio: ["ignore", "pipe", "pipe"] }
    );
    let stdout = "";
    let stderr = "";
    let finished = false;
    const timeout = setTimeout(() => {
      child.kill();
      finish(new Error("sqlite3 timed out reading VS Code workspace state"));
    }, 2_000);
    const finish = (error?: Error): void => {
      if (finished) {
        return;
      }
      finished = true;
      clearTimeout(timeout);
      if (error) {
        reject(error);
      } else {
        resolve(stdout.trim());
      }
    };

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk: string) => {
      stderr += chunk;
    });
    child.once("error", (error) => finish(error));
    child.once("close", (code) => {
      finish(
        code === 0
          ? undefined
          : new Error(stderr.trim() || `sqlite3 exited with code ${code}`)
      );
    });
  });
}
