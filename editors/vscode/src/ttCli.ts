import { spawn } from "node:child_process";
import { constants as fsConstants } from "node:fs";
import { access } from "node:fs/promises";
import { homedir } from "node:os";
import { delimiter, join, posix } from "node:path";

import * as vscode from "vscode";

import { parseHosts, parseRegistry, TtHost, TtRegistry } from "./model";

interface ExecuteOptions {
  showOutput?: boolean;
  token?: vscode.CancellationToken;
  cwd?: string;
  missingExecutableMessage?: string;
}

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

  async createTmuxSession(
    host: TtHost,
    registryHost: string,
    workspacePath: string,
    sessionName: string
  ): Promise<void> {
    const tmuxArgs = [
      "new-session",
      "-d",
      "-s",
      sessionName,
      "-c",
      workspacePath
    ];
    const title = `Creating tmux session ${sessionName}`;
    if (host.hostname === "localhost" || registryHost === "localhost") {
      await this.runExecutable("tmux", tmuxArgs, title);
      return;
    }
    await this.runExecutable(
      "ssh",
      [host.hostname, formatCommand("tmux", tmuxArgs)],
      title
    );
  }

  async killTmuxSession(
    host: TtHost,
    registryHost: string,
    sessionName: string
  ): Promise<void> {
    const tmuxArgs = ["kill-session", "-t", sessionName];
    const title = `Deleting tmux session ${sessionName}`;
    if (host.hostname === "localhost" || registryHost === "localhost") {
      await this.runExecutable("tmux", tmuxArgs, title);
      return;
    }
    await this.runExecutable(
      "ssh",
      [host.hostname, formatCommand("tmux", tmuxArgs)],
      title
    );
  }

  async sendTmuxCommand(
    host: TtHost,
    registryHost: string,
    sessionName: string,
    command: string
  ): Promise<void> {
    const literalKeys = [
      "send-keys",
      "-t",
      sessionName,
      "-l",
      "--",
      command
    ];
    const enterKey = ["send-keys", "-t", sessionName, "Enter"];
    const title = `Starting recovered work in ${sessionName}`;
    if (host.hostname === "localhost" || registryHost === "localhost") {
      await this.runExecutable("tmux", literalKeys, title);
      await this.runExecutable("tmux", enterKey, title);
      return;
    }
    await this.runExecutable(
      "ssh",
      [
        host.hostname,
        `${formatCommand("tmux", literalKeys)} && ${formatCommand("tmux", enterKey)}`
      ],
      title
    );
  }

  async createRepository(
    host: TtHost,
    registryHost: string,
    workspacePath: string,
    name: string
  ): Promise<string> {
    const repoPath = posix.join(workspacePath, name);
    const title = `Creating repository ${name}`;
    if (host.hostname === "localhost" || registryHost === "localhost") {
      if (await pathExists(repoPath)) {
        throw new TtCommandError(
          `Repository path already exists: ${repoPath}`,
          ["git", "init", "--", repoPath]
        );
      }
      await this.runExecutable("git", ["init", "--", repoPath], title);
      return repoPath;
    }

    const message = `Repository path already exists: ${repoPath}`;
    const command = [
      `[ ! -e ${shellQuote(repoPath)} ]`,
      `|| { echo ${shellQuote(message)} >&2; exit 1; }`,
      `&& ${formatCommand("git", ["init", "--", repoPath])}`
    ].join(" ");
    await this.runExecutable("ssh", [host.hostname, command], title);
    return repoPath;
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
    options: ExecuteOptions = {}
  ): Promise<{ stdout: string; stderr: string }> {
    const executable = await resolveExecutable();
    return this.executeProgram(executable, args, {
      ...options,
      missingExecutableMessage:
        `TT executable not found at '${executable}'. Install geno-tt or set genoTools.ttPath.`
    });
  }

  private async runExecutable(
    executable: string,
    args: string[],
    title: string
  ): Promise<string> {
    return vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title,
        cancellable: true
      },
      async (_progress, token) => {
        const result = await this.executeProgram(executable, args, {
          showOutput: true,
          token
        });
        return result.stdout;
      }
    );
  }

  private async executeProgram(
    executable: string,
    args: string[],
    options: ExecuteOptions = {}
  ): Promise<{ stdout: string; stderr: string }> {
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
              options.missingExecutableMessage ??
                `Executable not found: '${executable}'.`,
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

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch (error) {
    return !(
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "ENOENT"
    );
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
