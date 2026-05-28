# One-line loader. Source from any per-skill resource script:
#
#   LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../geno-tools/lib" && pwd)"
#   . "$LIB/load.sh"

_LIB_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
. "$_LIB_DIR/paths.sh"
. "$_LIB_DIR/common.sh"
. "$_LIB_DIR/config.sh"
. "$_LIB_DIR/registry.sh"
. "$_LIB_DIR/discovery.sh"
unset _LIB_DIR
