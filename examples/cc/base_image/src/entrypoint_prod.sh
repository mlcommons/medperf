[[ -n "${DATA_CONFIG:-}" ]] || { echo "Error: DATA_CONFIG not set or empty" >&2; exit 1; }
[[ -n "${MODEL_CONFIG:-}" ]] || { echo "Error: MODEL_CONFIG not set or empty" >&2; exit 1; }
[[ -n "${RESULT_CONFIG:-}" ]] || { echo "Error: RESULT_CONFIG not set or empty" >&2; exit 1; }
[[ -n "${RESULT_COLLECTOR:-}" ]] || { echo "Error: RESULT_COLLECTOR not set or empty" >&2; exit 1; }

[[ -n "${EXPECTED_DATA_HASH:-}" ]] || { echo "Error: EXPECTED_DATA_HASH not set or empty" >&2; exit 1; }
[[ -n "${EXPECTED_MODEL_HASH:-}" ]] || { echo "Error: EXPECTED_MODEL_HASH not set or empty" >&2; exit 1; }
[[ -n "${EXPECTED_RESULT_COLLECTOR_HASH:-}" ]] || { echo "Error: EXPECTED_RESULT_COLLECTOR_HASH not set or empty" >&2; exit 1; }

export TMP_FILES=/tmp/files

DATA_FILES=$TMP_FILES/data_files
MODEL_FILES=$TMP_FILES/model_files
RESULT_FILES=$TMP_FILES/results

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# setup assets
python3 $SCRIPT_DIR/setup_assets.py \
    --data-files $DATA_FILES \
    --model-files $MODEL_FILES

# run benchmark
bash $SCRIPT_DIR/benchmark/entrypoint.sh \
    --input-data $DATA_FILES/data \
    --input-labels $DATA_FILES/labels \
    --model-files $MODEL_FILES \
    --output-results $RESULT_FILES

# store results
python3 $SCRIPT_DIR/store_results.py \
    --result-files $RESULT_FILES