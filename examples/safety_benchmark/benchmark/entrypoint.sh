#!/bin/bash
set -eo pipefail

INPUT_DATA=""
INPUT_LABELS=""
MODEL_FILES=""
OUTPUT_RESULTS=""

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
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

[[ -n "$INPUT_DATA" ]] || { echo "Error: --input-data is required" >&2; exit 1; }
[[ -n "$INPUT_LABELS" ]] || { echo "Error: --input-labels is required" >&2; exit 1; }
[[ -n "$MODEL_FILES" ]] || { echo "Error: --model-files is required" >&2; exit 1; }
[[ -n "$OUTPUT_RESULTS" ]] || { echo "Error: --output-results is required" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/main.py" \
    --input-data "$INPUT_DATA" \
    --input-labels "$INPUT_LABELS" \
    --model-files "$MODEL_FILES" \
    --output-results "$OUTPUT_RESULTS"
