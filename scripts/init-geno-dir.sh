#!/usr/bin/env bash
# Materialize ~/.geno/ on session start so the geno-tools CLI and
# every skillset that reads ~/.geno/config.yaml has a config to read.
# Idempotent: skips the copy if the file already exists.
#
# Works under any coding CLI that supports a SessionStart hook —
# Claude Code exports ${CLAUDE_PLUGIN_ROOT}; Gemini CLI does not, so
# we fall back to resolving the plugin root from the script's own
# location (scripts/ sits one level under the plugin root).
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
