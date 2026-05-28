#!/usr/bin/env bash
# Show or clear the retro queue at ~/.geno/retro/queue.jsonl.
#
# Usage: trace-queue.sh [--clear] [--json]
#
# Replaces `geno-trace queue`.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
require_cmd jq

CLEAR=0
JSON=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --clear) CLEAR=1; shift ;;
    --json)  JSON=1;  shift ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

QUEUE="$RETRO_DIR/queue.jsonl"

if [[ $CLEAR == 1 ]]; then
  if [[ -f $QUEUE ]]; then
    rm -f "$QUEUE"
    printf 'retro queue cleared\n'
  else
    printf 'retro queue already empty\n'
  fi
  exit 0
fi

if [[ ! -f $QUEUE ]]; then
  printf 'retro queue is empty\n'
  exit 0
fi

ENTRIES=$(jq -c '. // empty' "$QUEUE" 2>/dev/null || true)
if [[ -z $ENTRIES ]]; then
  printf 'retro queue is empty\n'
  exit 0
fi

if [[ $JSON == 1 ]]; then
  printf '%s\n' "$ENTRIES" | jq -s '.'
  exit 0
fi

count=$(printf '%s\n' "$ENTRIES" | wc -l | tr -d ' ')
printf 'retro queue: %d entries\n' "$count"
printf '%s\n' "$ENTRIES" | jq -r '
  [(.queued_at[0:19]), .skill, .status] | @tsv' \
| awk -F'\t' '{ printf "  %s  %-40s  %s\n", $1, $2, $3 }'
