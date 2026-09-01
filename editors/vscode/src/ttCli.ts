import { spawn } from "node:child_process";
import { constants as fsConstants } from "node:fs";
import { access } from "node:fs/promises";
import { homedir } from "node:os";
import { delimiter, join, posix } from "node:path";

import * as vscode from "vscode";

import { parseHosts, parseRegistry, TtHost, TtRegistry } from "./model";

export class TtCommandError extends Error {
  constructor(
    message: string,
    readonly args: readonly string[],
    readonly exitCode?: number
  ) {
    super(message);
    this.name = "TtCommandError";
  }
}

export class TtCli {
  constructor(readonly output: vscode.OutputChannel) {}

  async hosts(): Promise<TtHost[]> {
    const result = await this.execute(["hosts"]);
    const hosts = parseHosts(result.stdout);
    if (hosts.length === 0) {
      throw new TtCommandError(
        "TT has no configured hosts. Run `tt add-host` before using the workspace explorer.",
        ["hosts"]
      );
    }
    return hosts;
  }

  async registry(host: TtHost): Promise<TtRegistry> {
    const result = await this.execute(this.forHost(host, ["registry", "show"]));
    return parseRegistry(result.stdout);
  }

  async refreshRegistry(host: TtHost): Promise<void> {
    await this.run(
      this.forHost(host, ["registry", "refresh"]),
      `Scanning TT workspaces on ${host.alias}`
    );
  }

  async run(args: string[], title: string, cwd?: string): Promise<string> {
    return vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title,
        cancellable: true
      },
      async (_progress, token) => {
        const result = await this.execute(args, { showOutput: true, token, cwd });
        return result.stdout;
      }
    );
  }

  forHost(host: TtHost, args: string[]): string[] {
    return ["-H", host.alias, ...args];
  }

  async resumeTmuxCommand(host: TtHost, workspace: string): Promise<string> {
    const executable = await resolveExecutable();
    return formatCommand(
      executable,
      this.forHost(host, ["tmux", "resume", workspace])
    );
  }

  async openTmuxCommand(
    host: TtHost,
    paneCurrentPath: string,
    sessionName: string
  ): Promise<string> {
    const executable = await resolveExecutable();
    return formatCommand(
      executable,
      this.forHost(host, [
        "tmux",
        posix.basename(paneCurrentPath),
        sessionName
      ])
    );
  }

  showOutput(): void {
    this.output.show(true);
  }

  private async execute(
    args: string[],
    options: {
      showOutput?: boolean;
      token?: vscode.CancellationToken;
      cwd?: string;
    } = {}
  ): Promise<{ stdout: string; stderr: string }> {
    const executable = await resolveExecutable();
    if (options.showOutput) {
      this.output.appendLine(`\n$ ${formatCommand(executable, args)}`);
      this.output.show(true);
    }

    return new Promise((resolve, reject) => {
      const child = spawn(executable, args, {
        cwd: options.cwd,
        env: process.env,
        shell: false
      });
      let stdout = "";
      let stderr = "";
      let cancelled = false;

      child.stdout.on("data", (chunk: Buffer) => {
        const text = chunk.toString();
        stdout += text;
        if (options.showOutput) {
          this.output.append(text);
        }
      });
      child.stderr.on("data", (chunk: Buffer) => {
        const text = chunk.toString();
        stderr += text;
        if (options.showOutput) {
          this.output.append(text);
        }
      });

      const cancellation = options.token?.onCancellationRequested(() => {
        cancelled = true;
        child.kill();
      });

      child.on("error", (error: NodeJS.ErrnoException) => {
        cancellation?.dispose();
        if (error.code === "ENOENT") {
          reject(
            new TtCommandError(
              `TT executable not found at '${executable}'. Install geno-tt or set genoTools.ttPath.`,
              args
            )
          );
          return;
        }
        reject(new TtCommandError(error.message, args));
      });
      child.on("close", (code) => {
        cancellation?.dispose();
        if (cancelled) {
          reject(new TtCommandError("TT command cancelled.", args, code ?? undefined));
          return;
        }
        if (code !== 0) {
          const detail = stderr.trim() || stdout.trim() || `TT exited with code ${code}.`;
          if (!options.showOutput) {
            this.output.appendLine(`\n$ ${formatCommand(executable, args)}`);
            this.output.appendLine(detail);
          }
          reject(new TtCommandError(detail, args, code ?? undefined));
          return;
        }
        resolve({ stdout, stderr });
      });
    });
  }
}

async function resolveExecutable(): Promise<string> {
  const configured = vscode.workspace
    .getConfiguration("genoTools")
    .get<string>("ttPath", "tt")
    .trim();
  if (configured !== "tt") {
    return configured;
  }

  for (const directory of (process.env.PATH ?? "").split(delimiter)) {
    if (!directory) {
      continue;
    }
    const candidate = join(directory, "tt");
    if (await isExecutable(candidate)) {
      return candidate;
    }
  }

  const userLocal = join(homedir(), ".local", "bin", "tt");
  return (await isExecutable(userLocal)) ? userLocal : "tt";
}

async function isExecutable(path: string): Promise<boolean> {
  try {
    await access(path, fsConstants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function formatCommand(executable: string, args: string[]): string {
  return [executable, ...args].map(shellQuote).join(" ");
}

function shellQuote(value: string): string {
  if (/^[A-Za-z0-9_./:@%+=,-]+$/.test(value)) {
    return value;
  }
  return `'${value.replaceAll("'", `'\\''`)}'`;
}
