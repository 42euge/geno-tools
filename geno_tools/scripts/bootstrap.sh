#!/usr/bin/env bash
# Bootstrap geno-tools at coding-agent session start.
#
# Two responsibilities, both idempotent and quiet (output goes to a log
# under ~/.geno/, never to the agent's stderr):
#
#   1. Materialize ~/.geno/config.yaml from config/defaults.yaml so the
#      CLI and every skillset that reads ~/.geno/config.yaml has a
#      config to read.
#   2. Self-install the geno-tools CLI onto PATH if it isn't already
#      there. Some coding agents don't auto-symlink the plugin's venv
#      binary; we fall back to pipx (preferred) or `pip install --user`
#      so the /gt-* slash commands and the `geno-tools` shell command
#      both work after a plugin install with no extra step.
#
# Works under any CLI that can run a shell command at session start —
# Claude Code exports ${CLAUDE_PLUGIN_ROOT}; for everything else we
# resolve the plugin root from this script's own location
# (geno_tools/scripts/ sits two levels under the plugin root).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="${CLAUDE_PLUGIN_ROOT:-${script_dir%/geno_tools/scripts}}"

target_dir="${HOME}/.geno"
target_file="${target_dir}/config.yaml"
default_config="${plugin_root}/geno_tools/config/defaults.yaml"
log_file="${target_dir}/bootstrap.log"

mkdir -p "${target_dir}"

if [[ ! -e "${target_file}" && -f "${default_config}" ]]; then
  cp "${default_config}" "${target_file}"
fi

# Keep each plugin manifest's `skills` array pointed at every category dir, so
# Claude Code's depth-1 plugin loader finds nested skills. Quiet + idempotent.
gen_skills="${plugin_root}/geno_tools/scripts/gen_plugin_skills.py"
if [[ -f "${gen_skills}" ]] && command -v python3 >/dev/null 2>&1; then
  python3 "${gen_skills}" >>"${log_file}" 2>&1 || true
fi

if command -v geno-tools >/dev/null 2>&1; then
  exit 0
fi

if [[ ! -f "${plugin_root}/pyproject.toml" ]]; then
  exit 0
fi

{
  echo "[$(date -u +%FT%TZ)] geno-tools not on PATH; installing from ${plugin_root}"
  if command -v pipx >/dev/null 2>&1; then
    pipx install --force "${plugin_root}"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user --quiet "${plugin_root}"
  else
    echo "no pipx or python3 found; cannot self-install geno-tools CLI"
  fi
} >>"${log_file}" 2>&1 || true
