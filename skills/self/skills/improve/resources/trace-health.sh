#!/usr/bin/env bash
# View or refresh skill health cards aggregated from trace JSONL.
#
# Usage:
#   trace-health.sh [--skill NAME] [--json]    # show one card / all
#   trace-health.sh --refresh                  # rebuild ~/.geno/health/*.json
#
# Replaces `geno-trace health`.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"
require_cmd jq

REFRESH=0
SKILL=""
JSON=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --refresh) REFRESH=1; shift ;;
    --skill)   SKILL=$2; shift 2 ;;
    --json)    JSON=1; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

if [[ $REFRESH == 1 ]]; then
  if [[ ! -d $TRACES_DIR ]]; then
    printf 'no traces found\n'
    exit 0
  fi
  ALL=$(find "$TRACES_DIR" -type f -name '*.jsonl' -exec cat {} +)
  if [[ -z $ALL ]]; then
    printf 'no traces found\n'
    exit 0
  fi
  mkdir -p "$HEALTH_DIR"
  CARDS=$(printf '%s\n' "$ALL" | jq -s '
    map(select(. != null))
    | group_by(.skill.name)
    | map({
        skill: .[0].skill.name,
        stats: {
          total_invocations: length,
          success_rate: ((map(select(.outcome.status == "success")) | length) / length | . * 1000 | floor / 1000),
          avg_tool_calls: ((map(.metrics.tool_calls) | add) / length | . * 10 | floor / 10),
          avg_thrashing: ((map(.metrics.thrashing_score) | add) / length | . * 1000 | floor / 1000),
          last_invoked: (sort_by(.timestamp) | .[-1].timestamp)
        },
        error_types: (map(select(.outcome.error_type != null) | .outcome.error_type)
                      | group_by(.) | map({key: .[0], value: length}) | from_entries),
        knowledge: {
          reads_from:  ([.[] | .knowledge.consumed[]?] | unique),
          writes_to:   ([.[] | .knowledge.produced[]?] | unique)
        },
        needs_retro: (
          (length >= 5)
          and ((map(select(.outcome.status == "success")) | length) / length < 0.7)
        )
      })')
  count=0
  needs_retro=()
  while IFS= read -r card; do
    [[ -z $card || $card == null ]] && continue
    name=$(printf '%s' "$card" | jq -r '.skill')
    [[ -z $name ]] && continue
    printf '%s\n' "$card" | jq '.' >"$HEALTH_DIR/$name.json"
    count=$((count+1))
    nr=$(printf '%s' "$card" | jq -r '.needs_retro')
    [[ $nr == "true" ]] && needs_retro+=("$name")
  done < <(printf '%s' "$CARDS" | jq -c '.[]')
  printf 'refreshed %d health cards\n' "$count"
  [[ ${#needs_retro[@]} -gt 0 ]] && printf 'needs retro: %s\n' "${needs_retro[*]}"
  exit 0
fi

if [[ -n $SKILL ]]; then
  CARD="$HEALTH_DIR/$SKILL.json"
  [[ -f $CARD ]] || { printf 'no health card for %s\n' "$SKILL"; exit 1; }
  if [[ $JSON == 1 ]]; then
    cat "$CARD"
  else
    jq -r '
      "\(.skill)
  invocations: \(.stats.total_invocations)
  success rate: \((.stats.success_rate * 100 | floor))%
  avg tool calls: \(.stats.avg_tool_calls)
  avg thrashing: \(.stats.avg_thrashing)
  last invoked: \(.stats.last_invoked[0:19])"
      + (if .needs_retro then "\n  ⚠ needs retro (success rate < 70%)" else "" end)
    ' "$CARD"
  fi
  exit 0
fi

if [[ ! -d $HEALTH_DIR ]]; then
  printf 'no health cards — run trace-health.sh --refresh first\n'
  exit 0
fi
CARDS=$(find "$HEALTH_DIR" -maxdepth 1 -name '*.json' -exec cat {} +)
[[ -z $CARDS ]] && { printf 'no health cards\n'; exit 0; }

if [[ $JSON == 1 ]]; then
  printf '%s\n' "$CARDS" | jq -s '.'
  exit 0
fi

printf '%-40s  %5s  %4s  %5s  %5s\n' "skill" "rate" "n" "tools" "retro"
printf -- '-%.0s' {1..65}; printf '\n'
printf '%s\n' "$CARDS" | jq -rs '
  sort_by(.skill) | .[] |
  [.skill,
   ((.stats.success_rate * 100 | floor | tostring) + "%"),
   (.stats.total_invocations | tostring),
   (.stats.avg_tool_calls | tostring),
   (if .needs_retro then "YES" else "" end)
  ] | @tsv' \
| awk -F'\t' '{ printf "%-40s  %5s  %4s  %5s  %5s\n", $1, $2, $3, $4, $5 }'
