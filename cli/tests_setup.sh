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
MEDPERF_STORAGE=~/.medperf
MEDPERF_LOG_STORAGE=~/.medperf_logs
SERVER_STORAGE_ID="$(echo $SERVER_URL | cut -d '/' -f 3 | sed -e 's/[.:]/_/g')"
TIMEOUT="${TIMEOUT:-30}"
VERSION_PREFIX="/api/v0"
LOGIN_SCRIPT="$(dirname $(realpath "$0"))/auto_login.sh"
ADMIN_LOGIN_SCRIPT="$(dirname $(dirname $(realpath "$0")))/server/auth_provider_token.py"
MOCK_TOKENS_FILE="$(dirname $(dirname $(realpath "$0")))/mock_tokens/tokens.json"

echo "Server URL: $SERVER_URL"
echo "Storage location: $MEDPERF_SUBSTORAGE"

# frequently used
clean() {
  echo "====================================="
  echo "Cleaning up medperf tmp files"
  echo "====================================="
  # move back storage
  rm -fr $DIRECTORY
  rm -fr $MEDPERF_STORAGE/**/$SERVER_STORAGE_ID
  # errors of the commands below are ignored
  medperf profile activate default
  medperf profile delete testbenchmark
  medperf profile delete testmodel
  medperf profile delete testdata
  medperf profile delete testagg
  medperf profile delete testdata1
  medperf profile delete testdata2
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
    echo "medperf log:"
    tail "$MEDPERF_LOG_STORAGE/medperf.log"
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
ASSETS_URL="https://raw.githubusercontent.com/hasan7n/mockcube/ab813a8142e1d9f2f215cb10cc59842dfc9b701c"

# datasets
DSET_A_URL="$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
DSET_B_URL="${ASSETS_URL}/assets/datasets/dataset_b.tar.gz"
DSET_C_URL="${ASSETS_URL}/assets/datasets/dataset_c.tar.gz"
DEMO_URL="${ASSETS_URL}/assets/datasets/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$ASSETS_URL/prep-sep/mlcube/mlcube.yaml"
PREP_PARAMS="$ASSETS_URL/prep-sep/mlcube/workspace/parameters.yaml"
PREP_TRAINING_MLCUBE="https://storage.googleapis.com/medperf-storage/testfl/mlcube.yaml"

# model cubes
FAILING_MODEL_MLCUBE="$ASSETS_URL/model-bug/mlcube/mlcube.yaml" # doesn't fail with association
MODEL_WITH_SINGULARITY="$ASSETS_URL/model-cpu/mlcube/mlcube_docker+singularity.yaml"
MODEL_MLCUBE="$ASSETS_URL/model-cpu/mlcube/mlcube.yaml"
MODEL_LOG_MLCUBE="$ASSETS_URL/model-debug-logging/mlcube/mlcube.yaml"
MODEL_ADD="$ASSETS_URL/assets/weights/weights1.tar.gz"
MODEL_SING_IMAGE="https://storage.googleapis.com/medperf-storage/mock-model-cpu.simg"

MODEL1_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters1.yaml"
MODEL2_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters2.yaml"
MODEL3_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters3.yaml"
MODEL4_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters4.yaml"

MODEL_LOG_NONE_PARAMS="$ASSETS_URL/model-debug-logging/mlcube/workspace/parameters_none.yaml"
MODEL_LOG_DEBUG_PARAMS="$ASSETS_URL/model-debug-logging/mlcube/workspace/parameters_debug.yaml"

# metrics cubes
METRIC_MLCUBE="$ASSETS_URL/metrics/mlcube/mlcube.yaml"
METRIC_PARAMS="$ASSETS_URL/metrics/mlcube/workspace/parameters.yaml"

# FL cubes
TRAIN_MLCUBE="https://raw.githubusercontent.com/hasan7n/medperf/19c80d88deaad27b353d1cb9bc180757534027aa/examples/fl/fl/mlcube/mlcube.yaml"
TRAIN_WEIGHTS="https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz"

# test users credentials
MODELOWNER="testmo@example.com"
DATAOWNER="testdo@example.com"
BENCHMARKOWNER="testbo@example.com"
ADMIN="testadmin@example.com"
DATAOWNER2="testdo2@example.com"
AGGOWNER="testao@example.com"

# local MLCubes for local compatibility tests
PREP_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/data_preparator/mlcube"
MODEL_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/model_custom_cnn/mlcube"
METRIC_LOCAL="$(dirname $(dirname $(realpath "$0")))/examples/chestxray_tutorial/metrics/mlcube"

TRAINING_CONFIG="$(dirname $(dirname $(realpath "$0")))/examples/fl/fl/mlcube/workspace/training_config.yaml"
