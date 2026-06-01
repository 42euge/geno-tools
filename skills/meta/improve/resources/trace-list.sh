#!/usr/bin/env bash
# Query stored traces, newest first, with optional filters.
#
# Usage: trace-list.sh [--skill NAME] [--status STATUS] [--since ISO_TS]
#                     [--limit N] [--json]
#
# Replaces `geno-trace list`.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
require_cmd jq

SKILL=""
STATUS=""
SINCE=""
LIMIT=50
JSON=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --skill)  SKILL=$2; shift 2 ;;
    --status) STATUS=$2; shift 2 ;;
    --since)  SINCE=$2; shift 2 ;;
    --limit)  LIMIT=$2; shift 2 ;;
    --json)   JSON=1; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -d $TRACES_DIR ]] || { printf 'no traces found\n'; exit 0; }

# Reverse-sorted file list, then reverse-iterate each file's lines.
mapfile -t FILES < <(find "$TRACES_DIR" -type f -name '*.jsonl' 2>/dev/null | LC_ALL=C sort -r)

# Stream filtered records (newest first) to jq for limiting + format.
STREAM=$(
  for f in "${FILES[@]}"; do
    tac -- "$f" 2>/dev/null
  done
)

FILTERED=$(printf '%s\n' "$STREAM" | jq -c \
  --arg skill "$SKILL" \
  --arg status "$STATUS" \
  --arg since "$SINCE" \
  --argjson limit "$LIMIT" '
  select(. != null) |
  select($skill == "" or .skill.name == $skill) |
  select($status == "" or .outcome.status == $status) |
  select($since == "" or .timestamp >= $since)' 2>/dev/null \
  | head -n "$LIMIT")

if [[ -z $FILTERED ]]; then
  printf 'no traces found\n'
  exit 0
fi

if [[ $JSON == 1 ]]; then
  printf '%s\n' "$FILTERED" | jq -s '.'
  exit 0
fi

printf '%s\n' "$FILTERED" | jq -r '
  [(.timestamp | .[0:19]),
   (.skill.name),
   (.outcome.status),
   (.metrics.tool_calls | tostring),
   (.metrics.errors | tostring)] | @tsv' \
| awk -F'\t' '{ printf "%s  %-40s  %-8s  tools=%s  errors=%s\n", $1, $2, $3, $4, $5 }'
