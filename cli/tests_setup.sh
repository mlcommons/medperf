#! /bin/sh
while getopts s:d:c:ft:rl: flag; do
  case "${flag}" in
  s) SERVER_URL=${OPTARG} ;;
  d) DIRECTORY=${OPTARG} ;;
  c) CLEANUP="true" ;;
  f) FRESH="true" ;;
  t) TIMEOUT=${OPTARG} ;;
  r) RESUME_TEST="true" ;;
  l) TEST_FROM_LINE=${OPTARG} ;;
  esac
done

SERVER_URL="${SERVER_URL:-https://localhost:8000}"
DIRECTORY="${DIRECTORY:-/tmp/medperf_test_files}"
CLEANUP="${CLEANUP:-false}"
RESUME_TEST="${RESUME_TEST:-false}"
FRESH="${FRESH:-false}"

# if resume test, read the test root from local file
if "${RESUME_TEST}"; then
  if [ -f "$(dirname $(realpath "$0"))/last_test_root.sh" ]; then
    . "$(dirname $(realpath "$0"))/last_test_root.sh"
    echo "Resuming test with test root: $TEST_ROOT"
  else
    echo "No last_test_root.sh file found to resume test"
    exit 1
  fi
else
  TEST_ROOT="/tmp/medperf_tests_$(date +%Y%m%d%H%M%S)"
  echo "TEST_ROOT=$TEST_ROOT" >"$(dirname $(realpath "$0"))/last_test_root.sh"
fi
export MEDPERF_CONFIG_STORAGE="$TEST_ROOT/medperf_config"
MEDPERF_CONFIG_PATH="$MEDPERF_CONFIG_STORAGE/config.yaml" # env var
MEDPERF_STORAGE="$TEST_ROOT/storage"
SNAPSHOTS_FOLDER=$TEST_ROOT/snapshots

MEDPERF_ROOT_REPO="$(dirname $(dirname $(realpath "$0")))"
MEDPERF_LOG_PATH=~/.medperf_logs/medperf.log
SERVER_STORAGE_ID="$(echo $SERVER_URL | cut -d '/' -f 3 | sed -e 's/[.:]/_/g')"
TIMEOUT="${TIMEOUT:-30}"
VERSION_PREFIX="/api/v0"
LOGIN_SCRIPT="$MEDPERF_ROOT_REPO/cli/auto_login.sh"
ADMIN_LOGIN_SCRIPT="$MEDPERF_ROOT_REPO/server/auth_provider_token.py"
MOCK_TOKENS_FILE="$MEDPERF_ROOT_REPO/mock_tokens/tokens.json"
SQLITE3_FILE="$MEDPERF_ROOT_REPO/server/db.sqlite3"
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

# datasets
DSET_A_URL="https://storage.googleapis.com/medperf-storage/medperf-integration-tests-mock-containers/dataset_a.tar.gz"
DSET_B_URL="https://storage.googleapis.com/medperf-storage/medperf-integration-tests-mock-containers/dataset_b.tar.gz"
DSET_C_URL="https://storage.googleapis.com/medperf-storage/medperf-integration-tests-mock-containers/dataset_c.tar.gz"
DEMO_URL="https://storage.googleapis.com/medperf-storage/medperf-integration-tests-mock-containers/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/prep-sep/container_config.yaml"
PREP_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/prep-sep/workspace/parameters.yaml"
PREP_TRAINING_MLCUBE="$MEDPERF_ROOT_REPO/examples/fl/prep/container_config.yaml"

# model cubes
FAILING_MODEL_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/model-bug/container_config.yaml" # doesn't fail with association
MODEL_WITH_SINGULARITY="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/container_config_as_singularity.yaml"
MODEL_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/container_config_as_docker.yaml"
MODEL_ARCHIVE_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/container_config_as_docker_archive.yaml"
MODEL_ENCRYPTED_ARCHIVE_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/container_config_as_encrypted_docker_archive.yaml"
MODEL_ENCRYPTED_SINGULARITY_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/container_config_as_encrypted_singularity.yaml"

MODEL_ADD="https://storage.googleapis.com/medperf-storage/medperf-integration-tests-mock-containers/weights1.tar.gz"

MODEL1_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/workspace/parameters1.yaml"
MODEL2_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/workspace/parameters2.yaml"
MODEL3_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/workspace/parameters3.yaml"
MODEL4_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/model-cpu/workspace/parameters4.yaml"

# chestxray tutorial models
CHESTXRAY_ENCRYPTED_MODEL="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/model_custom_cnn_encrypted/container_config.yaml"
CHESTXRAY_ENCRYPTED_MODEL_PARAMS="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/model_custom_cnn_encrypted/workspace/parameters.yaml"
CHESTXRAY_ENCRYPTED_MODEL_ADD="https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz"

# metrics cubes
METRIC_MLCUBE="$MEDPERF_ROOT_REPO/examples/tests/metrics/container_config.yaml"
METRIC_PARAMS="$MEDPERF_ROOT_REPO/examples/tests/metrics/workspace/parameters.yaml"

# FL cubes
TRAIN_MLCUBE="$MEDPERF_ROOT_REPO/examples/fl/fl/container_config.yaml"
TRAIN_WEIGHTS="https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz"
FLADMIN_MLCUBE="$MEDPERF_ROOT_REPO/examples/fl/fl_admin/container_config.yaml"

# Containers decryption keys
DOCKER_DECRYPTION_KEY="$MEDPERF_ROOT_REPO/examples/tests/assets/docker_decryption_key.bin"
SINGULARITY_DECRYPTION_KEY="$MEDPERF_ROOT_REPO/examples/tests/assets/singularity_decryption_key.bin"

# test users credentials
MODELOWNER="testmo@example.com"
DATAOWNER="testdo@example.com"
BENCHMARKOWNER="testbo@example.com"
ADMIN="testadmin@example.com"
DATAOWNER2="testdo2@example.com"
AGGOWNER="testao@example.com"
FLADMIN="testfladmin@example.com"
PRIVATEMODELOWNER="testpo@example.com"

# local MLCubes for local compatibility tests
PREP_LOCAL="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/data_preparator"
MODEL_LOCAL="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/model_custom_cnn"
METRIC_LOCAL="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/metrics"
PRIVATE_MODEL_LOCAL="$MEDPERF_ROOT_REPO/examples/chestxray_tutorial/model_custom_cnn_encrypted"

TRAINING_CONFIG="$MEDPERF_ROOT_REPO/examples/fl/fl/workspace/training_config.yaml"
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

if ! "${RESUME_TEST}"; then
  echo "Moving storage setting to a new folder: ${MEDPERF_STORAGE}"
  python $MEDPERF_ROOT_REPO/cli/cli_tests_move_storage.py $MEDPERF_CONFIG_PATH $MEDPERF_STORAGE
  checkFailed "Moving storage failed"
fi

# for test resuming
LAST_ENV_FILE="$(dirname $(realpath "$0"))/last_env.sh"
touch "$LAST_ENV_FILE"