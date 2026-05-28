#!/usr/bin/env bash
# Append a structured skill-trace JSONL record to ~/.geno/traces/YYYY/YYYY-MM.jsonl.
# Failed/partial traces are also queued for retro at ~/.geno/retro/queue.jsonl.
#
# Required: --skill, --status (success|partial|failure|abandoned)
# Optional: --skillset, --version, --error-type, --error-detail,
#           --tool-calls, --errors, --thrashing-score, --user-corrections,
#           --duration-turns, --task, --scope, --branch,
#           --consumed (repeatable), --produced (repeatable), --tags (repeatable)
#
# Replaces `geno-trace emit`.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

require_cmd jq

SKILL=""
STATUS=""
SKILLSET=""
VERSION=""
ERR_TYPE=""
ERR_DETAIL=""
TOOL_CALLS=0
ERRORS=0
THRASHING=0.0
USER_CORR=0
DUR_TURNS=0
TASK=""
SCOPE=""
BRANCH=""
declare -a CONSUMED=() PRODUCED=() TAGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --skill)            SKILL=$2; shift 2 ;;
    --status)           STATUS=$2; shift 2 ;;
    --skillset)         SKILLSET=$2; shift 2 ;;
    --version)          VERSION=$2; shift 2 ;;
    --error-type)       ERR_TYPE=$2; shift 2 ;;
    --error-detail)     ERR_DETAIL=$2; shift 2 ;;
    --tool-calls)       TOOL_CALLS=$2; shift 2 ;;
    --errors)           ERRORS=$2; shift 2 ;;
    --thrashing-score)  THRASHING=$2; shift 2 ;;
    --user-corrections) USER_CORR=$2; shift 2 ;;
    --duration-turns)   DUR_TURNS=$2; shift 2 ;;
    --task)             TASK=$2; shift 2 ;;
    --scope)            SCOPE=$2; shift 2 ;;
    --branch)           BRANCH=$2; shift 2 ;;
    --consumed)         CONSUMED+=("$2"); shift 2 ;;
    --produced)         PRODUCED+=("$2"); shift 2 ;;
    --tags)             TAGS+=("$2"); shift 2 ;;
    -h|--help)          sed -n '2,16p' "$0"; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -n $SKILL ]]  || die "--skill is required"
[[ -n $STATUS ]] || die "--status is required"
case $STATUS in success|partial|failure|abandoned) ;; *) die "--status must be one of success|partial|failure|abandoned" ;; esac

# Defaults derived from skill name.
if [[ -z $SKILLSET ]]; then
  case $SKILL in
    *-*) SKILLSET=${SKILL%-*} ;;
    *)   SKILLSET=$SKILL ;;
  esac
fi
[[ -n $VERSION ]] || VERSION=unknown

NOW=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
YEAR=${NOW:0:4}
MONTH=${NOW:5:2}
TRACE_DIR="$TRACES_DIR/$YEAR"
mkdir -p "$TRACE_DIR"
TRACE_FILE="$TRACE_DIR/$YEAR-$MONTH.jsonl"

ID="trace-$(printf '%s' "$NOW$$RANDOM" | md5sum | head -c 12)"

CONSUMED_JSON=$(printf '%s\n' "${CONSUMED[@]+"${CONSUMED[@]}"}" | jq -R . 2>/dev/null | jq -sc '.' 2>/dev/null || printf '[]')
PRODUCED_JSON=$(printf '%s\n' "${PRODUCED[@]+"${PRODUCED[@]}"}" | jq -R . 2>/dev/null | jq -sc '.' 2>/dev/null || printf '[]')
TAGS_JSON=$(    printf '%s\n' "${TAGS[@]+"${TAGS[@]}"}"         | jq -R . 2>/dev/null | jq -sc '.' 2>/dev/null || printf '[]')

PROJECT=${CLAUDE_PROJECT:-$(pwd)}
SESSION_ID=${CLAUDE_SESSION_ID:-}

TRACE=$(jq -nc \
  --arg id "$ID" \
  --arg ts "$NOW" \
  --arg session "$SESSION_ID" \
  --arg project "$PROJECT" \
  --arg name "$SKILL" \
  --arg skillset "$SKILLSET" \
  --arg version "$VERSION" \
  --arg status "$STATUS" \
  --arg etype "$ERR_TYPE" \
  --arg edetail "$ERR_DETAIL" \
  --argjson tool_calls "$TOOL_CALLS" \
  --argjson errors "$ERRORS" \
  --argjson thrashing "$THRASHING" \
  --argjson user_corr "$USER_CORR" \
  --argjson dur_turns "$DUR_TURNS" \
  --arg task "$TASK" \
  --arg scope "$SCOPE" \
  --arg branch "$BRANCH" \
  --argjson consumed "$CONSUMED_JSON" \
  --argjson produced "$PRODUCED_JSON" \
  --argjson tags "$TAGS_JSON" '
  {
    id: $id, timestamp: $ts, session_id: $session, project: $project,
    skill: { name: $name, skillset: $skillset, version: $version },
    outcome: {
      status: $status,
      error_type: (if $etype == "" then null else $etype end),
      error_detail: (if $edetail == "" then null else $edetail end)
    },
    metrics: {
      tool_calls: $tool_calls, errors: $errors,
      thrashing_score: $thrashing, user_corrections: $user_corr,
      duration_turns: $dur_turns
    },
    context: {
      task_id: (if $task == "" then null else $task end),
      scope:   (if $scope == "" then null else $scope end),
      branch:  (if $branch == "" then null else $branch end)
    },
    knowledge: { consumed: $consumed, produced: $produced },
    tags: $tags
  }')

printf '%s\n' "$TRACE" >>"$TRACE_FILE"
printf 'trace %s → %s\n' "$ID" "$TRACE_FILE"

if [[ $STATUS == failure || $STATUS == partial ]]; then
  mkdir -p "$RETRO_DIR"
  jq -nc --arg id "$ID" --arg s "$SKILL" --arg st "$STATUS" --arg q "$NOW" \
    '{trace_id:$id, skill:$s, status:$st, queued_at:$q}' \
    >>"$RETRO_DIR/queue.jsonl"
  printf 'queued for retro → %s/queue.jsonl\n' "$RETRO_DIR"
fi
