# User config helpers — reads ~/.geno/config.yaml.
# Source after paths.sh.

CONFIG_FILE="$GENO_DIR/config.yaml"

# Find packaged defaults.yaml relative to this lib dir.
_defaults_yaml() {
  local lib_dir
  lib_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  printf '%s/../../../config/defaults.yaml\n' "$lib_dir"
}

# Create ~/.geno/ and seed config.yaml from packaged defaults if missing.
ensure_config_dir() {
  mkdir -p "$GENO_DIR"
  if [[ ! -f $CONFIG_FILE ]]; then
    local defaults
    defaults=$(_defaults_yaml)
    if [[ -f $defaults ]]; then
      cp "$defaults" "$CONFIG_FILE"
    else
      cat >"$CONFIG_FILE" <<'EOF'
aliases:
  command_prefix: gt
discovery:
  sources:
    - kind: github
      org: 42euge
mode: user
autonomy: 1
EOF
    fi
  fi
}

# Read a config value via yq path. Usage: config_get '.aliases.command_prefix' [default]
config_get() {
  local path=$1
  local default=${2:-}
  if [[ ! -f $CONFIG_FILE ]] || ! command -v yq >/dev/null 2>&1; then
    printf '%s\n' "$default"
    return
  fi
  local val
  val=$(yq -r "$path // \"\"" "$CONFIG_FILE" 2>/dev/null || printf '')
  if [[ -z $val || $val == "null" ]]; then
    printf '%s\n' "$default"
  else
    printf '%s\n' "$val"
  fi
}

command_prefix() {
  config_get '.aliases.command_prefix' "gt"
}

# Print discovery sources as JSON array on a single line.
# Requires yq + jq for full schema fidelity.
config_discovery_sources_json() {
  if [[ ! -f $CONFIG_FILE ]]; then
    printf '[]\n'
    return
  fi
  if command -v yq >/dev/null 2>&1; then
    yq -o=json -I=0 '.discovery.sources // []' "$CONFIG_FILE" 2>/dev/null || printf '[]\n'
    return
  fi
  warn "yq not installed — cannot parse ~/.geno/config.yaml; install yq via 'pip install yq' or your package manager"
  printf '[]\n'
}
