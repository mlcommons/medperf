set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -v MEDPERF_ON_PREM ]]; then
    bash "$SCRIPT_DIR/entrypoint_dev.sh"
else
    bash "$SCRIPT_DIR/entrypoint_prod.sh"
fi
