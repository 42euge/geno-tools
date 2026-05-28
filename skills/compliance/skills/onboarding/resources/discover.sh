#!/usr/bin/env bash
# List candidate skillset repos from configured discovery sources.
#
# Usage: discover.sh [--dry-run]
#
# Replaces the Python `geno-tools discover` subcommand.

set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
. "$LIB/load.sh"

case ${1:-} in
  -h|--help) printf 'usage: discover.sh [--dry-run]\n'; exit 0 ;;
  --dry-run|'') ;;
  *) die "unknown option: $1" ;;
esac

ensure_config_dir

SOURCES=$(config_discovery_sources_json)
if [[ $SOURCES == "[]" ]]; then
  printf 'no discovery sources configured (~/.geno/config.yaml: discovery.sources)\n'
  exit 0
fi

found=0
while IFS=$'\t' read -r name url src has_skill; do
  [[ -z $name ]] && continue
  if [[ $has_skill == "true" ]]; then
    printf '  [%s] %-32s %s\n' "$src" "$name" "$url"
  else
    printf '  [%s] %-32s %s  (no SKILL.md — skipped)\n' "$src" "$name" "$url"
  fi
  found=1
done < <(discovery_candidates)

[[ $found == 0 ]] && printf 'no candidates found across configured sources\n'
