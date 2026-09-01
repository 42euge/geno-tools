import * as vscode from "vscode";

export type TerminalLinkKind = "attached" | "origin";

export interface TerminalLink {
  hostAlias: string;
  sessionName: string;
  kind: TerminalLinkKind;
}

const ATTACHED_TERMINAL_NAME = /^TT: ([^/]+)\/([A-Za-z0-9][A-Za-z0-9_-]*)$/;

export class TerminalLinkRegistry implements vscode.Disposable {
  private readonly links = new Map<vscode.Terminal, TerminalLink>();
  private readonly ignoredTerminals = new Set<vscode.Terminal>();

  markAttached(
    terminal: vscode.Terminal,
    hostAlias: string,
    sessionName: string
  ): void {
    this.ignoredTerminals.delete(terminal);
    this.links.set(terminal, { hostAlias, sessionName, kind: "attached" });
  }

  markOrigin(
    terminal: vscode.Terminal,
    hostAlias: string,
    sessionName: string
  ): void {
    this.ignoredTerminals.delete(terminal);
    this.links.set(terminal, { hostAlias, sessionName, kind: "origin" });
  }

  linkFor(terminal: vscode.Terminal): TerminalLink | undefined {
    if (this.ignoredTerminals.has(terminal)) {
      return undefined;
    }
    return this.links.get(terminal) ?? inferredAttachedLink(terminal);
  }

  hasAttachedTerminal(hostAlias: string, sessionName: string): boolean {
    return vscode.window.terminals.some((terminal) => {
      const link = this.linkFor(terminal);
      return link?.kind === "attached" &&
        link.hostAlias === hostAlias &&
        link.sessionName === sessionName;
    });
  }

  forget(terminal: vscode.Terminal): void {
    this.links.delete(terminal);
    this.ignoredTerminals.delete(terminal);
  }

  unlinkSession(hostAlias: string, sessionName: string): void {
    for (const terminal of vscode.window.terminals) {
      const link = this.linkFor(terminal);
      if (link?.hostAlias === hostAlias && link.sessionName === sessionName) {
        this.links.delete(terminal);
        this.ignoredTerminals.add(terminal);
      }
    }
  }

  dispose(): void {
    this.links.clear();
    this.ignoredTerminals.clear();
  }
}

function inferredAttachedLink(terminal: vscode.Terminal): TerminalLink | undefined {
  const match = terminal.name.match(ATTACHED_TERMINAL_NAME);
  return match
    ? {
        hostAlias: match[1],
        sessionName: match[2],
        kind: "attached"
      }
    : undefined;
}
