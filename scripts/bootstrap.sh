#!/usr/bin/env bash
# Bootstrap geno-tools at coding-agent session start.
#
# Single responsibility: materialize ~/.geno/config.yaml from
# config/defaults.yaml so the bash resource scripts that read
# ~/.geno/config.yaml have a config to read.
#
# Works under any CLI that can run a shell command at session start —
# Claude Code exports ${CLAUDE_PLUGIN_ROOT}; for everything else we
# resolve the plugin root from this script's own location (scripts/
# sits one level under the plugin root).

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="${CLAUDE_PLUGIN_ROOT:-${script_dir%/scripts}}"

target_dir="${HOME}/.geno"
target_file="${target_dir}/config.yaml"
default_config="${plugin_root}/config/defaults.yaml"

mkdir -p "${target_dir}"

if [[ ! -e "${target_file}" && -f "${default_config}" ]]; then
  cp "${default_config}" "${target_file}"
fi
