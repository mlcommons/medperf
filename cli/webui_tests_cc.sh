#!/bin/bash
# The confidential-computing workflow through the web UI.
#
# The browser counterpart of cli_tests_cc.sh: same parties, same mock CC
# backends, same chest X-ray benchmark, every step clicked rather than called.
# This script builds the environment and starts the web UI; the clicking is
# medperf/web_ui/tests/e2e_cc/webui_tests_cc.py, which is a plain script and
# not a pytest suite.
#
#   sh cli/webui_tests_cc.sh              records itself, port 8200
#   sh cli/webui_tests_cc.sh -p 8300      another port
#   sh cli/webui_tests_cc.sh -H           watch it live instead of recording
#   sh cli/webui_tests_cc.sh -o modelowner   the model owner runs the workload
#
# The operator is whoever runs the confidential workload, and it is not
# necessarily whoever the results are for -- both policies here release them to
# the data owner. With `-o modelowner` the operator never sees the results and
# the data owner collects them afterwards, which is the half `download_cc_results`
# exists for. Same switch, same name, as `CC_OPERATOR` in cli/tests_setup.sh.
#
# By default the browser draws on a virtual display and ffmpeg records that
# display for the whole run, leaving one mp4 in the artifacts directory.
#
# Everything around it -- the server, the database, what to check afterwards --
# is medperf/web_ui/tests/e2e_cc/RECIPE_mock.md.
#
# Kept to POSIX sh, like the other cli_tests_* scripts, so `sh` runs it.
set -e

PORT=8200
HEADED=""
CC_OPERATOR="${CC_OPERATOR:-dataowner}"
while getopts p:Ho: flag; do
    case "${flag}" in
        p) PORT=${OPTARG} ;;
        H) HEADED="--headed" ;;
        o) CC_OPERATOR=${OPTARG} ;;
        *) echo "usage: $0 [-p port] [-H] [-o dataowner|modelowner]" >&2; exit 1 ;;
    esac
done
export CC_OPERATOR

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

TEST_ROOT="/tmp/medperf_webui_cc_$(date +%Y%m%d%H%M%S)"
export MEDPERF_CONFIG_STORAGE="$TEST_ROOT/medperf_config"
MEDPERF_STORAGE="$TEST_ROOT/storage"
CC_MOCK_ROOT="${CC_MOCK_ROOT:-/tmp/medperf_cc_mock}"
export CC_MOCK_ROOT
ASSETS="$TEST_ROOT/files"
WEBUI_LOG="$TEST_ROOT/webui.log"

export CC_DATA_PATH="$ASSETS/sample_raw_data/images"
export CC_LABELS_PATH="$ASSETS/sample_raw_data/labels"
export CC_MODEL_TARBALL="$ASSETS/cnn_weights.tar.gz"
export WEBUI_ARTIFACTS="$TEST_ROOT/artifacts"

mkdir -p "$MEDPERF_CONFIG_STORAGE" "$MEDPERF_STORAGE" "$ASSETS" "$WEBUI_ARTIFACTS"

echo "Test root:   $TEST_ROOT"
echo "Operator:    $CC_OPERATOR"
echo "Web UI:      http://127.0.0.1:$PORT"
echo "Web UI log:  $WEBUI_LOG"
echo "Artifacts:   $WEBUI_ARTIFACTS"

WEBUI_PID=""
cleanup() {
    if [ -n "$WEBUI_PID" ] && kill -0 "$WEBUI_PID" 2>/dev/null; then
        kill "$WEBUI_PID" 2>/dev/null || true
        wait "$WEBUI_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

##########################################################
echo "====================================="
echo "Fetching the benchmark's assets"
echo "====================================="
wget -q -P "$ASSETS" "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_raw_data.tar.gz"
tar -xzf "$ASSETS/sample_raw_data.tar.gz" -C "$ASSETS"
wget -q -P "$ASSETS" "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz"

##########################################################
echo "====================================="
echo "Resetting the mock confidential backends"
echo "====================================="
rm -rf "$CC_MOCK_ROOT"
mkdir -p "$CC_MOCK_ROOT"

##########################################################
echo "====================================="
echo "Creating a profile for each party"
echo "====================================="
# The web UI activates profiles but does not create them, and each party needs
# its own: certificates and CC role settings live in the profile.
medperf profile ls > /dev/null          # writes the default config
python "$HERE/cli_tests_move_storage.py" "$MEDPERF_CONFIG_STORAGE/config.yaml" "$MEDPERF_STORAGE"
medperf profile activate local
medperf profile create -n testbenchmark
medperf profile create -n testmodel
medperf profile create -n testdata

##########################################################
echo "====================================="
echo "Starting the web UI"
echo "====================================="
medperf_webui --port "$PORT" > "$WEBUI_LOG" 2>&1 &
WEBUI_PID=$!

# Any answer means it is serving. Not `curl -f`: whether that page renders is
# the test's business, not this loop's.
for _ in $(seq 1 60); do
    if curl -s -m 5 -o /dev/null "http://127.0.0.1:$PORT/security_check"; then
        break
    fi
    if ! kill -0 "$WEBUI_PID" 2>/dev/null; then
        echo "The web UI exited before it served anything:" >&2
        tail -30 "$WEBUI_LOG" >&2
        exit 1
    fi
    sleep 1
done

##########################################################
echo "====================================="
echo "Driving the workflow"
echo "====================================="
# Not under `set -e`: a failed run is what the log below is for.
set +e
python "$REPO/cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc.py" \
    --port "$PORT" $HEADED
STATUS=$?
set -e

if [ "$STATUS" -ne 0 ]; then
    echo
    echo "Web UI log, last 40 lines:"
    tail -40 "$WEBUI_LOG"
fi

exit "$STATUS"
