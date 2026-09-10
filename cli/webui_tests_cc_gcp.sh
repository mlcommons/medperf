#!/bin/bash
# The confidential-computing workflow through the web UI, on Google Cloud.
#
# The cloud counterpart of cli/webui_tests_cc.sh: same parties, same chest
# X-ray benchmark, same clicks, with real GCP backends. What this script builds
# is one web UI per party rather than one for all three, because a GCP backend
# authenticates as whatever GOOGLE_APPLICATION_CREDENTIALS names and that is a
# property of a process, not of a MedPerf profile. The clicking is
# medperf/web_ui/tests/e2e_cc/webui_tests_cc_gcp.py.
#
#   bash cli/webui_tests_cc_gcp.sh            records itself, ports 8201..8203
#   bash cli/webui_tests_cc_gcp.sh -p 8300    another base port
#   bash cli/webui_tests_cc_gcp.sh -H         watch it live instead of recording
#
# The cloud resources are not created here. They are created once, by the
# terraform under examples/cc/admin_scripts/terraform, and named to this script
# through the environment below. Creating them, and everything else around a
# run, is medperf/web_ui/tests/e2e_cc/RECIPE_gcp.md.
set -e

PORT=8201
HEADED=""
while getopts p:H flag; do
    case "${flag}" in
        p) PORT=${OPTARG} ;;
        H) HEADED="--headed" ;;
        *) echo "usage: $0 [-p base_port] [-H]" >&2; exit 1 ;;
    esac
done

need() {
    if [ -z "${!1:-}" ]; then
        echo "$1 is not set. See examples/cc/admin_scripts/terraform/README.md" >&2
        exit 1
    fi
}

# `MPCC_BACKEND=mock` smoke tests everything this script does except the cloud:
# three web UIs, three credentials, a party switch. It needs none of the names.
MPCC_BACKEND="${MPCC_BACKEND:-gcp}"
export MPCC_BACKEND

if [ "$MPCC_BACKEND" = "gcp" ]; then
    for name in \
        MPCC_PROJECT_ID MPCC_PROJECT_NUMBER \
        MPCC_MODEL_BUCKET MPCC_MODEL_KEYRING MPCC_MODEL_KEY MPCC_MODEL_KEY_LOCATION \
        MPCC_MODEL_WIP MPCC_MODEL_WIP_PROVIDER MPCC_MODEL_ADC \
        MPCC_DATA_BUCKET MPCC_DATA_KEYRING MPCC_DATA_KEY MPCC_DATA_KEY_LOCATION \
        MPCC_DATA_WIP MPCC_DATA_WIP_PROVIDER MPCC_DATA_ADC \
        MPCC_WORKLOAD_SA_NAME MPCC_VM_NAME MPCC_VM_ZONE MPCC_COLLECTOR_BUCKET
    do
        need "$name"
    done
    # Impersonated credentials carry no project, and the storage client asks
    # for one. Every bucket here is in this project anyway.
    export GOOGLE_CLOUD_PROJECT="$MPCC_PROJECT_ID"
else
    export CC_MOCK_ROOT="${CC_MOCK_ROOT:-/tmp/medperf_cc_mock}"
    rm -rf "$CC_MOCK_ROOT"
    mkdir -p "$CC_MOCK_ROOT"
    MPCC_MODEL_ADC=""
    MPCC_DATA_ADC=""
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

TEST_ROOT="/tmp/medperf_webui_cc_gcp_$(date +%Y%m%d%H%M%S)"
ASSETS="$TEST_ROOT/files"

export CC_DATA_PATH="$ASSETS/sample_raw_data/images"
export CC_LABELS_PATH="$ASSETS/sample_raw_data/labels"
export CC_MODEL_TARBALL="$ASSETS/cnn_weights.tar.gz"
export WEBUI_ARTIFACTS="$TEST_ROOT/artifacts"
export WEBUI_PARTIES="$TEST_ROOT/parties.json"

mkdir -p "$ASSETS" "$WEBUI_ARTIFACTS"

echo "Test root:  $TEST_ROOT"
echo "Artifacts:  $WEBUI_ARTIFACTS"

PIDS=""
cleanup() {
    for pid in $PIDS; do
        kill "$pid" 2>/dev/null || true
    done
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
echo "Starting one web UI per party"
echo "====================================="
# Each gets a configuration storage, a MedPerf profile and a port of its own,
# and the two that touch the cloud get their own credentials. Nothing is shared
# but the MedPerf server they all talk to.
start_party() {
    name="$1"; email="$2"; profile="$3"; port="$4"; adc="$5"

    storage="$TEST_ROOT/$name"
    export MEDPERF_CONFIG_STORAGE="$storage/config"
    mkdir -p "$MEDPERF_CONFIG_STORAGE" "$storage/storage"

    medperf profile ls > /dev/null
    python "$HERE/cli_tests_move_storage.py" \
        "$MEDPERF_CONFIG_STORAGE/config.yaml" "$storage/storage" > /dev/null
    medperf profile activate local
    medperf profile create -n "$profile"
    medperf profile activate "$profile"

    if [ -n "$adc" ]; then
        GOOGLE_APPLICATION_CREDENTIALS="$adc" medperf_webui --port "$port" \
            > "$storage/webui.log" 2>&1 &
    else
        # Whatever credentials this shell holds are the admin's, and this party
        # has no business with them.
        env -u GOOGLE_APPLICATION_CREDENTIALS medperf_webui --port "$port" \
            > "$storage/webui.log" 2>&1 &
    fi
    pid=$!
    PIDS="$PIDS $pid"

    # Any answer means it is serving. Not `curl -f`: whether that page renders
    # is the test's business, not this loop's.
    for _ in $(seq 1 60); do
        if curl -s -m 5 -o /dev/null "http://127.0.0.1:$port/security_check"; then
            break
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "The $name web UI exited before it served anything:" >&2
            tail -30 "$storage/webui.log" >&2
            exit 1
        fi
        sleep 1
    done

    if ! curl -s -m 5 -o /dev/null "http://127.0.0.1:$port/security_check"; then
        echo "The $name web UI never answered on port $port:" >&2
        tail -30 "$storage/webui.log" >&2
        exit 1
    fi

    printf '  %-9s port %s  log %s\n' "$name" "$port" "$storage/webui.log"
    cat >> "$TEST_ROOT/parties.part" <<EOF
  "$name": {"email": "$email", "port": $port, "config_storage": "$MEDPERF_CONFIG_STORAGE"},
EOF
}

: > "$TEST_ROOT/parties.part"
start_party benchmark testbo@example.com testbenchmark "$PORT"           ""
start_party model     testmo@example.com testmodel     "$((PORT + 1))"   "$MPCC_MODEL_ADC"
start_party data      testdo@example.com testdata      "$((PORT + 2))"   "$MPCC_DATA_ADC"

{
    echo "{"
    sed '$ s/,$//' "$TEST_ROOT/parties.part"
    echo "}"
} > "$WEBUI_PARTIES"

##########################################################
echo "====================================="
echo "Driving the workflow"
echo "====================================="
# Not under `set -e`: a failed run is what the logs below are for.
set +e
python "$REPO/cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc_gcp.py" $HEADED
STATUS=$?
set -e

if [ "$STATUS" -ne 0 ]; then
    for name in benchmark model data; do
        echo
        echo "$name web UI log, last 30 lines:"
        tail -30 "$TEST_ROOT/$name/webui.log"
    done
fi

exit "$STATUS"
