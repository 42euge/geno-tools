#!/usr/bin/env bash
# Scan discovery sources, find uninstalled candidates, and append them to the
# candidate queue at ~/.geno/discovery/candidates.jsonl.
#
# Usage: scan.sh [--namespace <prefix>] [--dry-run]
#
# Replaces the Python `geno-tools scan` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

NS=""
DRY=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --namespace) NS=${2:-}; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) printf 'usage: scan.sh [--namespace <prefix>] [--dry-run]\n'; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

ensure_config_dir

SOURCES=$(config_discovery_sources_json)
if [[ $SOURCES == "[]" ]]; then
  printf 'no discovery sources configured (~/.geno/config.yaml: discovery.sources)\n'
  exit 0
fi

mkdir -p "$DISCOVERY_DIR"
RESULT=$(discovery_scan "$NS" "$DRY")

if [[ -z $RESULT ]]; then
  printf 'no new candidates found\n'
  exit 0
fi

count=$(printf '%s\n' "$RESULT" | wc -l | tr -d ' ')
action=queued
[[ $DRY == 1 ]] && action=found
printf '%s %s new candidate(s):\n' "$action" "$count"
printf '%s\n' "$RESULT" | while IFS=$'\t' read -r name url src; do
  printf '  [%s] %-32s %s\n' "$src" "$name" "$url"
done

[[ $DRY == 1 ]] || printf '\ncandidates written to %s/candidates.jsonl\n' "$DISCOVERY_DIR"
