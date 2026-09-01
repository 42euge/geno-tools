#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: persist-agent-session.sh [--dry-run] [SESSION_NAME]

Create a detached tmux session and resume the current Codex or Claude Code
conversation inside it. SESSION_NAME is optional.
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

session_name=""
dry_run=false
while (($# > 0)); do
  case "$1" in
    --dry-run)
      dry_run=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      [[ -z "$session_name" ]] || die "only one session name may be supplied"
      session_name="$1"
      ;;
  esac
  shift
done

command -v tmux >/dev/null 2>&1 || die "tmux is not installed or not on PATH"

if [[ -n "${TMUX:-}" ]]; then
  current_session="$(tmux display-message -p '#S')"
  echo "Already persistent in tmux session '$current_session'."
  echo "Attach later with: tmux attach-session -t '$current_session'"
  exit 0
fi

agent=""
agent_bin=""
session_id=""
resume_command=""
if [[ -n "${CODEX_SESSION_ID:-${CODEX_THREAD_ID:-}}" ]]; then
  agent="codex"
  session_id="${CODEX_SESSION_ID:-${CODEX_THREAD_ID}}"
  agent_bin="$(command -v codex || true)"
  [[ -n "$agent_bin" ]] || die "the current session is Codex, but 'codex' is not on PATH"
  resume_command="exec env -u CODEX_SESSION_ID -u CODEX_THREAD_ID -u CODEX_CI '$agent_bin' resume '$session_id'"
elif [[ -n "${CLAUDE_CODE_SESSION_ID:-}" ]]; then
  agent="claude"
  session_id="$CLAUDE_CODE_SESSION_ID"
  agent_bin="$(command -v claude || true)"
  [[ -n "$agent_bin" ]] || die "the current session is Claude Code, but 'claude' is not on PATH"
  resume_command="exec env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_SESSION_ID -u CLAUDECODE '$agent_bin' --resume '$session_id'"
else
  die "no current agent session ID found; run this from a Codex or Claude Code session"
fi

[[ "$session_id" =~ ^[A-Za-z0-9_-]+$ ]] || die "the current agent session ID has an unexpected format"

if [[ -n "$session_name" ]]; then
  [[ "$session_name" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] ||
    die "session names may contain only letters, digits, hyphens, and underscores"
  if tmux has-session -t "=$session_name" 2>/dev/null; then
    die "tmux session '$session_name' already exists"
  fi
else
  directory="$(basename "$PWD")"
  directory="$(printf '%s' "$directory" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_-]+/-/g; s/^-+//; s/-+$//')"
  base_name="${directory:-agent}-$agent"
  session_name="$base_name"
  suffix=2
  while tmux has-session -t "=$session_name" 2>/dev/null; do
    session_name="$base_name-$suffix"
    ((suffix += 1))
  done
fi

if [[ "$dry_run" == true ]]; then
  echo "Would create tmux session '$session_name' in '$PWD'."
  echo "Would run: $agent resume <current-session-id>"
  exit 0
fi

tmux new-session -d -s "$session_name" -c "$PWD"
tmux send-keys -t "$session_name:0.0" -l "$resume_command"
tmux send-keys -t "$session_name:0.0" Enter

echo "Created tmux session '$session_name' for the current $agent conversation."
echo "Attach with: tmux attach-session -t '$session_name'"
