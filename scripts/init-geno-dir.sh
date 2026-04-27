#!/usr/bin/env bash
# Materialize ~/.geno/ on session start so the geno-tools CLI and
# every skillset that reads ~/.geno/config.yaml has a config to read.
# Idempotent: skips the copy if the file already exists.
set -euo pipefail

target_dir="${HOME}/.geno"
target_file="${target_dir}/config.yaml"
default_config="${CLAUDE_PLUGIN_ROOT:-}/config/defaults.yaml"

mkdir -p "${target_dir}"

if [[ ! -e "${target_file}" && -f "${default_config}" ]]; then
  cp "${default_config}" "${target_file}"
fi
