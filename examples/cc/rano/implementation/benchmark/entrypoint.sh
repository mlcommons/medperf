#!/bin/bash
set -eo pipefail

# Default values
INPUT_DATA=""
INPUT_LABELS=""
MODEL_FILES=""
OUTPUT_RESULTS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --input-data)
            INPUT_DATA="$2"
            shift 2
            ;;
        --input-labels)
            INPUT_LABELS="$2"
            shift 2
            ;;
        --model-files)
            MODEL_FILES="$2"
            shift 2
            ;;
        --output-results)
            OUTPUT_RESULTS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$INPUT_DATA" ]]; then
    echo "Error: --input-data is required"
    exit 1
fi

if [[ -z "$INPUT_LABELS" ]]; then
    echo "Error: --input-labels is required"
    exit 1
fi

if [[ -z "$MODEL_FILES" ]]; then
    echo "Error: --model-files is required"
    exit 1
fi

if [[ -z "$OUTPUT_RESULTS" ]]; then
    echo "Error: --output-results is required"
    exit 1
fi

# run benchmark
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export USER=appuser


TEMP_PREDICTIONS_DIR="/tmp/predictions"
mkdir -p "$TEMP_PREDICTIONS_DIR"

start_time=$(date +%s)

bash $SCRIPT_DIR/inference/entrypoint.sh \
    --postopp_pardir "$INPUT_DATA" \
    --inference_output_dir "$TEMP_PREDICTIONS_DIR" \
    --source_plans_dir "$MODEL_FILES"

end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo "Inference step took ${elapsed} seconds"

OUTPUT_RESULT_FILE="$OUTPUT_RESULTS/results.yaml"
OUTPUT_LOCAL_RESULTS="$OUTPUT_RESULTS/local_results"
mkdir -p "$OUTPUT_LOCAL_RESULTS"

start_time=$(date +%s)

python $SCRIPT_DIR/metrics/evaluate.py \
    --postopp_pardir "$INPUT_LABELS" \
    --inference_output_dir "$TEMP_PREDICTIONS_DIR" \
    --output_metrics "$OUTPUT_RESULT_FILE" \
    --local_outputs "$OUTPUT_LOCAL_RESULTS"

end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo "Metrics evaluation step took ${elapsed} seconds"
