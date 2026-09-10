# Confidential end-to-end run of the safety benchmark.
#
# The same shape as cli_tests_cc.sh -- mock CC backends, three users, one
# end_to_end_script benchmark -- with the safety benchmark's components in
# place of the chest X-ray ones. What it exercises that the other does not is a
# script container that loads a language model inside the workload and relays a
# benchmark service's prompts to it.

# import setup
. "$(dirname $(realpath "$0"))/tests_setup.sh"

##########################################################
# Safety benchmark components. The CC configs and policies come from
# tests_setup.sh: they name the mock backend and a filesystem root, and say
# nothing about what is being benchmarked.
##########################################################
SAFETY_ROOT="$MEDPERF_ROOT_REPO/examples/safety_benchmark"
SAFETY_PREP="$SAFETY_ROOT/prep/container_config.yaml"
SAFETY_PREP_PARAMS="$SAFETY_ROOT/prep/workspace/parameters_test.yaml"
SAFETY_SCRIPT="$SAFETY_ROOT/container_config.yaml"

# Set by the caller.
#
# The model under test comes from a local path: that is what makes it an asset
# nobody has a copy of, which is what makes the run confidential. The reference
# model has to come from a URL instead -- a local-path asset requires CC, and
# the reference model is run by whoever is testing compatibility, on their own
# machine, against a dataset that is not configured for CC yet.
SAFETY_MODEL_TARBALL="${SAFETY_MODEL_TARBALL:?Set SAFETY_MODEL_TARBALL to the weights tarball}"
SAFETY_MODEL_URL="${SAFETY_MODEL_URL:?Set SAFETY_MODEL_URL to a URL serving that tarball}"
SAFETY_DEMO_URL="${SAFETY_DEMO_URL:?Set SAFETY_DEMO_URL to the demo dataset tarball URL}"

# The benchmark has no prompts of its own: it relays a run from a benchmark
# service. baas-client's mock_server is a toy one to point this at. The
# workload reaches it from inside a container, so the address has to be one a
# container can resolve -- the docker bridge gateway, not localhost.
SAFETY_BAAS_URL="${SAFETY_BAAS_URL:?Set SAFETY_BAAS_URL to a benchmark service, e.g. http://172.17.0.1:8500}"
SAFETY_BAAS_KEY="${SAFETY_BAAS_KEY:-medperf-e2e-key}"

# The data owner's whole dataset: which service, and the key that reaches it.
SAFETY_RAW_DATA="$TEST_ROOT/safety_connection"
mkdir -p "$SAFETY_RAW_DATA"
cat > "$SAFETY_RAW_DATA/connection.yaml" <<EOF
url: $SAFETY_BAAS_URL
key: $SAFETY_BAAS_KEY
model_id: safety-model-under-test
EOF

##########################################################
echo "=========================================="
echo "Printing MedPerf version"
echo "=========================================="
print_eval medperf --version
checkFailed "MedPerf version failed"
##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Creating test profiles for each user"
echo "=========================================="
print_eval medperf profile activate local
checkFailed "local profile creation failed"

print_eval medperf profile create -n testbenchmark
checkFailed "testbenchmark profile creation failed"
print_eval medperf profile create -n testmodel
checkFailed "testmodel profile creation failed"
print_eval medperf profile create -n testdata
checkFailed "testdata profile creation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Resetting the mock confidential backends"
echo "====================================="
rm -rf $CC_MOCK_ROOT
mkdir -p $CC_MOCK_ROOT
##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Login each user"
echo "=========================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

print_eval medperf auth login -e $BENCHMARKOWNER
checkFailed "testbenchmark login failed"

print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

print_eval medperf auth login -e $MODELOWNER
checkFailed "testmodel login failed"

print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf auth login -e $DATAOWNER
checkFailed "testdata login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate benchmarkowner profile"
echo "====================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit dataset preparation container"
echo "====================================="
print_eval medperf container submit --name safety-prep -m $SAFETY_PREP -p $SAFETY_PREP_PARAMS --operational
checkFailed "Prep container submission failed"
PREP_UID=$(medperf container ls | grep safety-prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit benchmark script container"
echo "====================================="
print_eval medperf container submit --name safety-script -m $SAFETY_SCRIPT --operational
checkFailed "Benchmark script container submission failed"
SCRIPT_UID=$(medperf container ls | grep safety-script | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "SCRIPT_UID=$SCRIPT_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit the reference model asset"
echo "====================================="
print_eval medperf model submit --name safety-reference-model --asset-url $SAFETY_MODEL_URL --operational
checkFailed "Reference model submission failed"
REF_MODEL_UID=$(medperf model ls | grep safety-reference-model | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "REF_MODEL_UID=$REF_MODEL_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit the safety benchmark"
echo "====================================="
# Compatibility tests are skipped: they run the script container on the local
# medium, which MedPerf gives no network, and the run needs to reach the
# benchmark service. The flag also skips them at both association steps below.
print_eval medperf benchmark submit --name safety-bmk --description AILuminate-shaped-safety-benchmark --demo-url $SAFETY_DEMO_URL --data-preparation-container $PREP_UID --reference-model $REF_MODEL_UID --topology end_to_end_script --benchmark-script $SCRIPT_UID --skip-compatibility-tests --operational
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep safety-bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "BMK_UID=$BMK_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate modelowner profile"
echo "====================================="
print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit the model under test"
echo "====================================="
print_eval medperf model submit --name safety-model-under-test --asset-path "$SAFETY_MODEL_TARBALL" --operational
checkFailed "Model submission failed"
MODEL_UID=$(medperf model ls | grep safety-model-under-test | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL_UID=$MODEL_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Associate the model to the benchmark"
echo "====================================="
# Skipped, because the benchmark was registered with
# --skip-compatibility-tests: a local-medium run has no network and this
# benchmark cannot run without reaching the service.
print_eval medperf model associate -m $MODEL_UID -b $BMK_UID -y
checkFailed "Model association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Get and submit a client certificate for the data owner"
echo "====================================="
print_eval medperf certificate get_client_certificate --key_type RSA
checkFailed "get certificate failed"

print_eval medperf certificate submit_client_certificate --key_type RSA -y
checkFailed "Failed to submit Data Owner Certificate"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Get and submit a client certificate for the model owner"
echo "====================================="
print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

print_eval medperf certificate get_client_certificate --key_type RSA
checkFailed "get certificate failed"

print_eval medperf certificate submit_client_certificate --key_type RSA -y
checkFailed "Failed to submit Model Owner Certificate"

print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit the service connection as a dataset"
echo "====================================="
# There are no labels -- the service grades -- so both paths are the folder
# holding the one connection.yaml.
print_eval medperf dataset submit -p $PREP_UID -d $SAFETY_RAW_DATA -l $SAFETY_RAW_DATA --name='safety_service' --description='AILuminate-benchmark-service-connection' --location='mock-location' -y
checkFailed "Data submission step failed"
DSET_UID=$(medperf dataset ls | grep safety_service | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
echo "DSET_UID=$DSET_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Prepare the connection"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_UID
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Mark the connection operational"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_UID -y
checkFailed "Data set operational step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Associate the connection to the benchmark"
echo "====================================="
print_eval medperf dataset associate -d $DSET_UID -b $BMK_UID -y
checkFailed "Data association step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve both associations (benchmark owner)"
echo "====================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

print_eval medperf association approve -b $BMK_UID -d $DSET_UID
checkFailed "Dataset association approval failed"

print_eval medperf association approve -b $BMK_UID -m $MODEL_UID
checkFailed "Model association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Configure the model for CC (model owner)"
echo "====================================="
print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

print_eval medperf confidential configure_model_for_cc -m $MODEL_UID -c $MODEL_CC_CONFIG -p $MODEL_CC_POLICY
checkFailed "Model configure_for_cc failed"

print_eval medperf confidential update_model_cc_policy -m $MODEL_UID
checkFailed "Model update_cc_policy failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Configure the connection for CC (data owner)"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf confidential configure_dataset_for_cc -d $DSET_UID -c $DATASET_CC_CONFIG -p $DATASET_CC_POLICY
checkFailed "Dataset configure_for_cc failed"

print_eval medperf confidential update_dataset_cc_policy -d $DSET_UID
checkFailed "Dataset update_cc_policy failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Setup where the results are received (by $CC_COLLECTOR_PROFILE)"
echo "====================================="
print_eval medperf profile activate $CC_COLLECTOR_PROFILE
checkFailed "$CC_COLLECTOR_PROFILE profile activation failed"

print_eval medperf confidential setup_cc_collector -c $COLLECTOR_CC_CONFIG
checkFailed "Setup CC result collector failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Setup CC operator ($CC_OPERATOR is operator)"
echo "====================================="
print_eval medperf profile activate $CC_OPERATOR_PROFILE
checkFailed "$CC_OPERATOR_PROFILE profile activation failed"

print_eval medperf confidential setup_cc_operator -c $OPERATOR_CC_CONFIG
checkFailed "Setup CC operator failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Run the benchmark ($CC_OPERATOR is operator)"
echo "====================================="
if [ "$CC_OPERATOR" = "modelowner" ]; then
  # Nothing else in this test writes to $DIRECTORY -- unlike cli_tests_cc.sh,
  # the model tarball comes from $SAFETY_MODEL_TARBALL -- so it may not exist,
  # and tee failing here would fail the run after a workload that succeeded.
  mkdir -p "$DIRECTORY"
  print_eval medperf model run_benchmark -b $BMK_UID -m $MODEL_UID 2>&1 | tee "$DIRECTORY/cc_safety_run.log"
else
  print_eval medperf dataset run_benchmark -b $BMK_UID -d $DSET_UID
fi
checkFailed "Benchmark execution failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Collect the results (by $CC_COLLECTOR_PROFILE)"
echo "====================================="
if [ "$CC_OPERATOR" = "modelowner" ]; then
  EXECUTION_UID=$(grep -o "download_cc_results -e [0-9]*" "$DIRECTORY/cc_safety_run.log" | tail -n 1 | tr -s " " | cut -d " " -f 3)
  echo "EXECUTION_UID=$EXECUTION_UID"
  if [ -z "$EXECUTION_UID" ]; then
    echo "The operator was not told which execution to hand over"
    exit 1
  fi

  print_eval medperf profile activate $CC_COLLECTOR_PROFILE
  checkFailed "$CC_COLLECTOR_PROFILE profile activation failed"

  print_eval medperf confidential download_cc_results -e $EXECUTION_UID
  checkFailed "Collecting the results failed"

  print_eval medperf result submit -r $EXECUTION_UID -y
  checkFailed "Submitting the collected results failed"
else
  echo "The operator collected their own results inline."
fi
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Show the grades"
echo "====================================="
print_eval medperf result ls
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Logout users"
echo "====================================="
print_eval medperf profile activate testbenchmark
medperf auth logout

medperf profile activate testmodel
medperf auth logout

medperf profile activate testdata
medperf auth logout
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Delete test profiles"
echo "====================================="
print_eval medperf profile activate default
checkFailed "default profile activation failed"

print_eval medperf profile delete testbenchmark
print_eval medperf profile delete testmodel
print_eval medperf profile delete testdata
##########################################################

if ${CLEANUP}; then
  clean
fi
