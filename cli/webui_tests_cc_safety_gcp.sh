#!/bin/bash
# The safety benchmark's confidential workflow through the web UI, on Google Cloud.
#
# The safety counterpart of cli/webui_tests_cc_gcp.sh: same three parties, same
# one-web-UI-per-party structure, same recorder, with the AILuminate-shaped
# safety benchmark in place of the chest X-ray one. What it exercises that the
# chest X-ray run does not is a run whose two halves belong to two different
# people: the model owner operates the VM, and the data owner -- the only party
# either policy releases results to -- collects afterwards by clicking. The
# clicking is medperf/web_ui/tests/e2e_cc/webui_tests_cc_safety_gcp.py.
#
#   bash cli/webui_tests_cc_safety_gcp.sh            records itself, ports 8201..8203
#   bash cli/webui_tests_cc_safety_gcp.sh -p 8300    another base port
#   bash cli/webui_tests_cc_safety_gcp.sh -H         watch it live instead of recording
#   bash cli/webui_tests_cc_safety_gcp.sh -a gpu     run on the H100 VM, not the CPU one
#
# Two things have to be handed to it, because neither belongs in a repository:
#
#   SAFETY_MODEL_TARBALL   the weights under test, a local tarball
#   MPCC_*                 the cloud resources, when MPCC_BACKEND=gcp
#
# The benchmark itself has no prompts: it relays a run from a benchmark service.
# Point SAFETY_BAAS_URL at one, or leave it unset and this starts the toy server
# from the baas-client repository beside this one (SAFETY_BAAS_SERVER names it
# elsewhere, SAFETY_BAAS_PORT moves it, SAFETY_BAAS_KEY sets the key).
#
# SAFETY_IMAGE_PREFIX points both container configs at a registry of your own,
# for testing an image you built rather than the published one.
#
# The model under test comes from a local path -- that is what makes it an
# asset nobody has a copy of, and so a run that requires CC. The *reference*
# model must come from a URL instead, because it is run on the local medium
# during association. The same tarball serves both: this script puts it, and a
# tarball of the demo prompt set, behind a local HTTP server for the duration
# of the run.
#
# The cloud resources are not created here. They are created once, by the
# terraform under examples/cc/admin_scripts/terraform, and named to this script
# through the environment below. Creating them, and everything else around a
# run, is medperf/web_ui/tests/e2e_cc/RECIPE_gcp_safety.md.
set -e

PORT=8201
HEADED=""
# cpu or gpu. The two confidential VMs differ only in which one the operator is
# pointed at, so this choice is a VM name and a zone and nothing else.
ACCEL="${MPCC_ACCEL:-cpu}"
while getopts p:Ha: flag; do
    case "${flag}" in
        p) PORT=${OPTARG} ;;
        H) HEADED="--headed" ;;
        a) ACCEL=${OPTARG} ;;
        *) echo "usage: $0 [-p base_port] [-H] [-a cpu|gpu]" >&2; exit 1 ;;
    esac
done

case "$ACCEL" in
    cpu) ACCEL_VM_NAME="mpcc-e2e-safety-vm";     ACCEL_VM_ZONE="us-west1-b" ;;
    gpu) ACCEL_VM_NAME="mpcc-e2e-safety-gpu-vm"; ACCEL_VM_ZONE="us-central1-a" ;;
    *)   echo "-a / MPCC_ACCEL must be cpu or gpu, not '$ACCEL'" >&2; exit 1 ;;
esac
# Each accelerator has its own terraform stack and so its own VM. Naming either
# variable by hand still wins, for a VM built some other way.
export MPCC_VM_NAME="${MPCC_VM_NAME:-$ACCEL_VM_NAME}"
export MPCC_VM_ZONE="${MPCC_VM_ZONE:-$ACCEL_VM_ZONE}"

need() {
    if [ -z "${!1:-}" ]; then
        echo "$1 is not set. See medperf/web_ui/tests/e2e_cc/RECIPE_gcp_safety.md" >&2
        exit 1
    fi
}

need SAFETY_MODEL_TARBALL
if [ ! -f "$SAFETY_MODEL_TARBALL" ]; then
    echo "SAFETY_MODEL_TARBALL is not a file: $SAFETY_MODEL_TARBALL" >&2
    exit 1
fi

# `MPCC_BACKEND=mock` smoke tests everything this script does except the cloud:
# three web UIs, three credentials, a party switch, the operator/collector
# split. It needs none of the names.
MPCC_BACKEND="${MPCC_BACKEND:-gcp}"
export MPCC_BACKEND

if [ "$MPCC_BACKEND" = "gcp" ]; then
    for name in \
        MPCC_PROJECT_ID MPCC_PROJECT_NUMBER \
        MPCC_MODEL_BUCKET MPCC_MODEL_KEYRING MPCC_MODEL_KEY MPCC_MODEL_KEY_LOCATION \
        MPCC_MODEL_WIP MPCC_MODEL_WIP_PROVIDER MPCC_MODEL_ADC \
        MPCC_DATA_BUCKET MPCC_DATA_KEYRING MPCC_DATA_KEY MPCC_DATA_KEY_LOCATION \
        MPCC_DATA_WIP MPCC_DATA_WIP_PROVIDER MPCC_DATA_ADC \
        MPCC_WORKLOAD_SA_NAME MPCC_COLLECTOR_BUCKET
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
SAFETY="$REPO/examples/safety_benchmark"

TEST_ROOT="/tmp/medperf_webui_cc_safety_gcp_$(date +%Y%m%d%H%M%S)"
SERVE="$TEST_ROOT/serve"
SERVE_PORT="${MPCC_SERVE_PORT:-8100}"

# The data owner's whole dataset: one connection.yaml naming the benchmark
# service and the key that reaches it, written below. There are no labels, so
# both paths are the same folder.
CONNECTION="$TEST_ROOT/connection"
export CC_DATA_PATH="$CONNECTION"
export CC_LABELS_PATH="$CONNECTION"
export CC_MODEL_TARBALL="$SAFETY_MODEL_TARBALL"
export WEBUI_ARTIFACTS="$TEST_ROOT/artifacts"
export WEBUI_PARTIES="$TEST_ROOT/parties.json"

mkdir -p "$SERVE" "$WEBUI_ARTIFACTS" "$CONNECTION"

echo "Test root:  $TEST_ROOT"
echo "Artifacts:  $WEBUI_ARTIFACTS"
echo "Operator:   $ACCEL, $MPCC_VM_NAME in $MPCC_VM_ZONE"

PIDS=""
cleanup() {
    for pid in $PIDS; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

##########################################################
echo "====================================="
echo "The benchmark service"
echo "====================================="
# The workload has no prompts of its own: it relays a run from a benchmark
# service. Name one that is already running with SAFETY_BAAS_URL, or let this
# start the toy server from the baas-client repository beside this one.
#
# The workload reaches it from inside a container, so the address has to be one
# a container can resolve -- the docker bridge gateway, not localhost. Binding
# the toy server to that same address keeps it off every other interface.
BAAS_KEY="${SAFETY_BAAS_KEY:-medperf-e2e-key}"
BAAS_URL="${SAFETY_BAAS_URL:-}"

if [ -z "$BAAS_URL" ]; then
    MOCK_BAAS="${SAFETY_BAAS_SERVER:-$REPO/../baas-client/mock_server/server.py}"
    if [ ! -f "$MOCK_BAAS" ]; then
        echo "No benchmark service. Either set SAFETY_BAAS_URL to one, or set" >&2
        echo "SAFETY_BAAS_SERVER to baas-client's mock_server/server.py." >&2
        echo "Looked for it at: $MOCK_BAAS" >&2
        exit 1
    fi

    GATEWAY=$(docker network inspect bridge -f '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null)
    if [ -z "$GATEWAY" ]; then
        echo "Could not read the docker bridge gateway; is docker running?" >&2
        exit 1
    fi
    BAAS_PORT="${SAFETY_BAAS_PORT:-8500}"
    BAAS_URL="http://$GATEWAY:$BAAS_PORT"

    BAAS_MOCK_KEY="$BAAS_KEY" python "$MOCK_BAAS" --host "$GATEWAY" --port "$BAAS_PORT" \
        > "$TEST_ROOT/baas.log" 2>&1 &
    PIDS="$PIDS $!"

    for _ in $(seq 1 30); do
        if curl -sf -m 5 -o /dev/null "$BAAS_URL/up"; then
            break
        fi
        sleep 1
    done
    if ! curl -sf -m 5 -o /dev/null "$BAAS_URL/up"; then
        echo "The toy benchmark service never answered on $BAAS_URL:" >&2
        tail -20 "$TEST_ROOT/baas.log" >&2
        echo "(is port $BAAS_PORT taken? set SAFETY_BAAS_PORT)" >&2
        exit 1
    fi
    echo "  toy server $BAAS_URL  (log $TEST_ROOT/baas.log)"
else
    echo "  service    $BAAS_URL"
fi

# The data owner's dataset, written the way one would write it by hand.
cat > "$CONNECTION/connection.yaml" <<EOF
url: $BAAS_URL
key: $BAAS_KEY
model_id: safety-model-under-test
EOF

##########################################################
echo "====================================="
echo "Serving the reference model and the demo dataset"
echo "====================================="
# Only this machine fetches these. The confidential VM never does: it reads the
# *encrypted* asset out of the owner's bucket.
ln -sf "$SAFETY_MODEL_TARBALL" "$SERVE/model.tar.gz"
tar -czf "$SERVE/safety_demo.tar.gz" -C "$SAFETY" demo

python -m http.server "$SERVE_PORT" --bind 127.0.0.1 --directory "$SERVE" \
    > "$TEST_ROOT/http.log" 2>&1 &
PIDS="$PIDS $!"

export SAFETY_MODEL_URL="http://127.0.0.1:$SERVE_PORT/model.tar.gz"
export SAFETY_DEMO_URL="http://127.0.0.1:$SERVE_PORT/safety_demo.tar.gz"

for _ in $(seq 1 30); do
    if curl -sf -m 5 -o /dev/null "$SAFETY_MODEL_URL"; then
        break
    fi
    sleep 1
done
if ! curl -sf -m 5 -o /dev/null "$SAFETY_MODEL_URL"; then
    echo "Nothing is serving $SAFETY_MODEL_URL:" >&2
    tail -20 "$TEST_ROOT/http.log" >&2
    echo "(is port $SERVE_PORT taken? set MPCC_SERVE_PORT)" >&2
    exit 1
fi
echo "  model  $SAFETY_MODEL_URL"
echo "  demo   $SAFETY_DEMO_URL"

##########################################################
echo "====================================="
echo "The two container configs"
echo "====================================="
# Registering a container pulls the image it names and records that registry's
# digest, so a locally built image has to be in a registry the client can pull
# from. SAFETY_IMAGE_PREFIX rewrites both configs to point at one -- e.g.
# localhost:5555 with `docker run -d -p 5555:5000 registry:2`. Unset, the
# published mlcommons images are used and nothing is rewritten.
export SAFETY_PREP_CONFIG="$TEST_ROOT/prep_container_config.yaml"
export SAFETY_SCRIPT_CONFIG="$TEST_ROOT/script_container_config.yaml"
cp "$SAFETY/prep/container_config.yaml" "$SAFETY_PREP_CONFIG"
cp "$SAFETY/container_config.yaml" "$SAFETY_SCRIPT_CONFIG"

if [ -n "${SAFETY_IMAGE_PREFIX:-}" ]; then
    sed -i "s|^image: mlcommons/|image: $SAFETY_IMAGE_PREFIX/|" \
        "$SAFETY_PREP_CONFIG" "$SAFETY_SCRIPT_CONFIG"
fi
grep -h '^image:' "$SAFETY_PREP_CONFIG" "$SAFETY_SCRIPT_CONFIG" | sed 's/^/  /'

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
python "$REPO/cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc_safety_gcp.py" $HEADED
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
