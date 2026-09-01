#!/usr/bin/env bash
# Install the geno-tools CLI onto PATH — the explicit, loud counterpart to the
# silent SessionStart bootstrap. Idempotent: safe to re-run.
#
# Resolves the plugin root from CLAUDE_PLUGIN_ROOT, else from this script's
# location (skills/setup/ sits two levels under the plugin root).
set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="${CLAUDE_PLUGIN_ROOT:-${script_dir%/skills/setup}}"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$1"; }

echo "geno-tools setup — installing the CLI from ${plugin_root}"

# 1. Seed ~/.geno/config.yaml (same as bootstrap).
mkdir -p "${HOME}/.geno"
default_config="${plugin_root}/geno_tools/core/config/defaults.yaml"
if [[ ! -e "${HOME}/.geno/config.yaml" && -f "${default_config}" ]]; then
  cp "${default_config}" "${HOME}/.geno/config.yaml"
  ok "seeded ~/.geno/config.yaml"
else
  ok "~/.geno/config.yaml present"
fi

# 2. Already on PATH? Done.
if command -v geno-tools >/dev/null 2>&1; then
  ok "geno-tools already on PATH ($(command -v geno-tools))"
  geno-tools --version 2>/dev/null || true
  exit 0
fi

if [[ ! -f "${plugin_root}/pyproject.toml" ]]; then
  err "no pyproject.toml at ${plugin_root}; cannot install the CLI"
  exit 1
fi

# 3. Locate pipx. It's often installed but not on a non-interactive PATH
#    (e.g. ~/Library/Python/3.x/bin on macOS, ~/.local/bin), so probe those
#    before deciding it's missing.
find_pipx() {
  command -v pipx 2>/dev/null && return 0
  for p in "${HOME}/.local/bin/pipx" "${HOME}"/Library/Python/*/bin/pipx; do
    [[ -x "$p" ]] && { echo "$p"; return 0; }
  done
  return 1
}

pipx_bin="$(find_pipx)" || pipx_bin=""

# On Homebrew Python, `pip install --user` is blocked by PEP 668, so pipx is the
# reliable installer — install it (preferring brew) only if truly absent.
if [[ -z "${pipx_bin}" ]]; then
  warn "pipx not found; installing it"
  if command -v brew >/dev/null 2>&1; then
    brew install pipx && brew --prefix >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user --quiet pipx 2>/dev/null \
      || python3 -m pip install --user --break-system-packages --quiet pipx
  else
    err "no brew or python3 to install pipx; install pipx manually, then re-run"
    exit 1
  fi
  pipx_bin="$(find_pipx)" || pipx_bin="python3 -m pipx"
else
  ok "found pipx: ${pipx_bin}"
fi

# 4. Install the CLI with pipx and make sure its bin dir is on PATH.
${pipx_bin} ensurepath >/dev/null 2>&1 || true
${pipx_bin} install --force "${plugin_root}"

# 5. Verify — pipx drops binaries in ~/.local/bin; surface PATH issues loudly.
hash -r 2>/dev/null || true
if command -v geno-tools >/dev/null 2>&1; then
  ok "geno-tools installed: $(command -v geno-tools)"
  geno-tools --version 2>/dev/null || true
  ok "setup complete — try: geno-tools discover"
else
  warn "geno-tools installed but not yet on PATH for this shell."
  warn "It's at ~/.local/bin/geno-tools. Add ~/.local/bin to PATH (pipx ensurepath)"
  warn "and open a new shell, or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
