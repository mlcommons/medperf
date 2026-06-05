set -eo pipefail

# run benchmark
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash $SCRIPT_DIR/benchmark/entrypoint.sh \
    --input-data /mlcommons/volumes/data \
    --input-labels /mlcommons/volumes/labels \
    --model-files /mlcommons/volumes/model_files \
    --output-results /mlcommons/volumes/results
