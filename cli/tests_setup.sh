#! /bin/bash
while getopts s:d:c:ft: flag; do
  case "${flag}" in
  s) SERVER_URL=${OPTARG} ;;
  d) DIRECTORY=${OPTARG} ;;
  c) CLEANUP="true" ;;
  f) FRESH="true" ;;
  t) TIMEOUT=${OPTARG} ;;
  esac
done

SERVER_URL="${SERVER_URL:-https://localhost:8000}"
DIRECTORY="${DIRECTORY:-/tmp/medperf_test_files}"
CLEANUP="${CLEANUP:-false}"
FRESH="${FRESH:-false}"

TEST_ROOT="/tmp/medperf_tests_$(date +%Y%m%d%H%M%S)"
export MEDPERF_CONFIG_PATH="$TEST_ROOT/config.yaml" # env var
MEDPERF_STORAGE="$TEST_ROOT/storage"
SNAPSHOTS_FOLDER=$TEST_ROOT/snapshots

MEDPERF_LOG_PATH=~/.medperf_logs/medperf.log
SERVER_STORAGE_ID="$(echo $SERVER_URL | cut -d '/' -f 3 | sed -e 's/[.:]/_/g')"
TIMEOUT="${TIMEOUT:-30}"
VERSION_PREFIX="/api/v0"
LOGIN_SCRIPT="$(dirname $(realpath "$0"))/auto_login.sh"
ADMIN_LOGIN_SCRIPT="$(dirname $(dirname $(realpath "$0")))/server/auth_provider_token.py"
MOCK_TOKENS_FILE="$(dirname $(dirname $(realpath "$0")))/mock_tokens/tokens.json"
SQLITE3_FILE="$(dirname $(dirname $(realpath "$0")))/server/db.sqlite3"
echo "Server URL: $SERVER_URL"

print_eval() {
  local timestamp=$(date +%m%d%H%M%S)
  local formatted_cmd=$(echo "$@" | sed 's/[^a-zA-Z0-9]\+/_/g' | cut -c 1-50)
  LAST_SNAPSHOT_PATH="$SNAPSHOTS_FOLDER/${timestamp}_${formatted_cmd}.sqlite3"
  cp $SQLITE3_FILE "$LAST_SNAPSHOT_PATH"
  echo ">> $@"
  eval "$@"
  # local exit_code=$?
  # echo "Exit code: $exit_code"
  # return $exit_code
}
# frequently used
clean() {
  echo "====================================="
  echo "Cleaning up medperf tmp files"
  echo "====================================="
  # move back storage
  rm -fr $DIRECTORY
  rm -fr $TEST_ROOT
}
checkFailed() {
  EXITSTATUS="$?"
  if [ -n "$2" ]; then
    EXITSTATUS="1"
  fi
  if [ $EXITSTATUS -ne "0" ]; then
    if [ $EXITSTATUS -eq 124 ]; then
      echo "Process timed out"
    fi
    echo $1
    echo "Test root path: $TEST_ROOT"
    echo "Config path: $MEDPERF_CONFIG_PATH"
    echo "Storage path: $MEDPERF_STORAGE"
    echo "Snapshot before failed command: $LAST_SNAPSHOT_PATH"
    echo "medperf log $MEDPERF_LOG_PATH:"
    tail $MEDPERF_LOG_PATH
    if ${CLEANUP}; then
      clean
    fi
    exit 1
  fi
}

checkSucceeded() {
  if [ "$?" -eq 0 ]; then
    i_am_a_command_that_does_not_exist_and_hence_changes_the_last_exit_status_to_nonzero
  fi
  checkFailed "$1"
}

if ${FRESH}; then
  clean
fi
##########################################################
########################## Setup #########################
##########################################################
ASSETS_URL="https://raw.githubusercontent.com/hasan7n/mockcube/63454ef4bb96f1879a549e2131ab6361a702e8e1"

# datasets
DSET_A_URL="$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
DSET_B_URL="${ASSETS_URL}/assets/datasets/dataset_b.tar.gz"
DSET_C_URL="${ASSETS_URL}/assets/datasets/dataset_c.tar.gz"
DEMO_URL="${ASSETS_URL}/assets/datasets/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$ASSETS_URL/prep-sep/container_config.yaml"
PREP_PARAMS="$ASSETS_URL/prep-sep/workspace/parameters.yaml"
PREP_TRAINING_MLCUBE="https://storage.googleapis.com/medperf-storage/testfl/mlcube.yaml"

# model cubes
FAILING_MODEL_MLCUBE="$ASSETS_URL/model-bug/mlcube/mlcube.yaml" # doesn't fail with association
MODEL_WITH_SINGULARITY="$ASSETS_URL/model-cpu/container_config_as_singularity.yaml"
MODEL_MLCUBE="$ASSETS_URL/model-cpu/container_config_as_docker.yaml"
MODEL_LOG_MLCUBE="$ASSETS_URL/model-debug-logging/mlcube/mlcube.yaml"
MODEL_ADD="$ASSETS_URL/assets/weights/weights1.tar.gz"

MODEL1_PARAMS="$ASSETS_URL/model-cpu/workspace/parameters1.yaml"
MODEL2_PARAMS="$ASSETS_URL/model-cpu/workspace/parameters2.yaml"
MODEL3_PARAMS="$ASSETS_URL/model-cpu/workspace/parameters3.yaml"
MODEL4_PARAMS="$ASSETS_URL/model-cpu/workspace/parameters4.yaml"

MODEL_LOG_NONE_PARAMS="$ASSETS_URL/model-debug-logging/mlcube/workspace/parameters_none.yaml"
MODEL_LOG_DEBUG_PARAMS="$ASSETS_URL/model-debug-logging/mlcube/workspace/parameters_debug.yaml"

# metrics cubes
METRIC_MLCUBE="$ASSETS_URL/metrics/container_config.yaml"
METRIC_PARAMS="$ASSETS_URL/metrics/workspace/parameters.yaml"

# FL cubes
TRAIN_MLCUBE="https://raw.githubusercontent.com/hasan7n/medperf/19c80d88deaad27b353d1cb9bc180757534027aa/examples/fl/fl/mlcube/mlcube.yaml"
TRAIN_WEIGHTS="https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz"
FLADMIN_MLCUBE="https://raw.githubusercontent.com/hasan7n/medperf/bc431ffe6c3b761b28674816e6f26511e8b27042/examples/fl/fl_admin/mlcube/mlcube.yaml"

# test users credentials
MODELOWNER="testmo@example.com"
DATAOWNER="testdo@example.com"
BENCHMARKOWNER="testbo@example.com"
ADMIN="testadmin@example.com"
DATAOWNER2="testdo2@example.com"
AGGOWNER="testao@example.com"
FLADMIN="testfladmin@example.com"

# local MLCubes for local compatibility tests
PREP_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/data_preparator/mlcube"
MODEL_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/model_custom_cnn/mlcube"
METRIC_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/metrics/mlcube"

TRAINING_CONFIG="$(dirname $(dirname $(realpath "$0")))/examples/fl/fl/mlcube/workspace/training_config.yaml"
# create storage folders
mkdir -p "$TEST_ROOT"
mkdir -p "$MEDPERF_STORAGE"
mkdir -p "$SNAPSHOTS_FOLDER"

echo "Test root path: $TEST_ROOT"
echo "Config path: $MEDPERF_CONFIG_PATH"
echo "Snapshots path: $SNAPSHOTS_FOLDER"
echo "Storage path: $MEDPERF_STORAGE"

# test env folder preparation
echo "creating config at $MEDPERF_CONFIG_PATH"
print_eval medperf profile ls
checkFailed "Creating config failed"

echo "Moving storage setting to a new folder: ${MEDPERF_STORAGE}"
python $(dirname $(realpath "$0"))/cli_tests_move_storage.py $MEDPERF_CONFIG_PATH $MEDPERF_STORAGE
checkFailed "Moving storage failed"
