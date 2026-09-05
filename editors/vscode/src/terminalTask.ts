export interface TerminalTaskEvidence {
  label: string;
  mentions: number;
  sources: string[];
}

export const TERMINAL_TASK_FOCUS_INSTRUCTIONS = [
  "Name the enduring subject, feature, artifact, or intended outcome, not a temporary action such as reviewing, checking, running, testing, or listing.",
  "Use this evidence priority: a later explicit human goal; then a specific active or uncommitted feature identifier corroborated by a branch, worktree, spec, or acceptance file; then another specific subject; and only as a fallback a generic recent activity.",
  "The terminal context may include taskEvidence extracted from branch and document identifiers. Repeated matching identifiers are stronger than a one-off status request.",
  "A clean, default, unrelated, or stale branch is weak evidence. A clear later human goal overrides it.",
  "Convert identifiers like feat/operator-console-layout into natural words such as operator console layout and omit category prefixes."
] as const;

export function terminalTaskEvidence(history: string): TerminalTaskEvidence[] {
  const evidence = new Map<
    string,
    { mentions: number; sources: Set<string> }
  >();
  const add = (identifier: string, source: string): void => {
    const label = identifier
      .replace(/[._/-]+/gu, " ")
      .replace(/\s+/gu, " ")
      .trim()
      .toLowerCase();
    if (!label) {
      return;
    }
    const current = evidence.get(label) ?? {
      mentions: 0,
      sources: new Set<string>()
    };
    current.mentions += 1;
    current.sources.add(source);
    evidence.set(label, current);
  };

  for (const match of history.matchAll(
    /(?<![/\\\w-])(?:feat(?:ure)?|fix|bugfix|chore|docs|refactor|test)\/([a-z0-9][a-z0-9._/-]*)/giu
  )) {
    add(match[1], "branch");
  }
  for (const match of history.matchAll(
    /(?:^|[/\\])(?:acceptance|specs?)\/([a-z0-9][a-z0-9._-]*)\.md\b/gimu
  )) {
    add(match[1], "acceptance file");
  }

  return Array.from(evidence, ([label, value]) => ({
    label,
    mentions: value.mentions,
    sources: [...value.sources]
  }))
    .sort((left, right) =>
      right.sources.length - left.sources.length ||
      right.mentions - left.mentions ||
      left.label.localeCompare(right.label)
    )
    .slice(0, 5);
}
