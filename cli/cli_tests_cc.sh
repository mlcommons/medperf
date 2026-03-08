# import setup
. "$(dirname $(realpath "$0"))/tests_setup.sh"

##########################################################
################### Start Testing ########################
##########################################################

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
echo "Retrieving mock datasets"
echo "====================================="
echo "downloading files to $DIRECTORY"
print_eval wget -P $DIRECTORY "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_raw_data.tar.gz"
print_eval tar -xzvf $DIRECTORY/sample_raw_data.tar.gz -C $DIRECTORY
print_eval chmod -R a+w $DIRECTORY
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Retrieving mock models"
echo "====================================="
echo "downloading files to $DIRECTORY"
print_eval wget -P $DIRECTORY "$CHESTXRAY_MOBILENET_MODEL"
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
echo "Submit prep container (by benchmark owner)"
echo "====================================="
print_eval medperf container submit --name cc-prep -m $CHESTXRAY_DATA_PREP -p $CHESTXRAY_DATA_PREP_PARAMS --operational
checkFailed "Prep container submission failed"
PREP_UID=$(medperf container ls | grep cc-prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit evaluator container (cc chestxray)"
echo "====================================="
print_eval medperf container submit --name cc-eval -m $CHESTXRAY_SCRIPT --operational
checkFailed "Evaluator container submission failed"
EVAL_UID=$(medperf container ls | grep cc-eval | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "EVAL_UID=$EVAL_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit CNN weights as an Asset (reference model asset)"
echo "====================================="

print_eval medperf model submit --name cc-cnn-weights --asset-url $CHESTXRAY_CNN_MODEL --operational
checkFailed "CNN model submission failed"
REF_MODEL_UID=$(medperf model ls | grep cc-cnn-weights | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "REF_MODEL_UID=$REF_MODEL_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit CC benchmark"
echo "====================================="
print_eval medperf benchmark submit --name cc-bmk --description "CC-benchmark-test" --demo-url $CHESTXRAY_DEMO_URL --data-preparation-container $PREP_UID --reference-model $REF_MODEL_UID --evaluator-container $EVAL_UID --operational
checkFailed "CC Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep cc-bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
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
echo "Submit MobileNetV2 weights as an Asset"
echo "====================================="
print_eval medperf model submit --name cc-mobilenet-weights --asset-path "$DIRECTORY/cnn_weights.tar.gz" --operational
checkFailed "MobileNetV2 model submission failed"
MOBILENET_MODEL_UID=$(medperf model ls | grep cc-mobilenet-weights | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MOBILENET_MODEL_UID=$MOBILENET_MODEL_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Associate MobileNetV2 model to CC benchmark"
echo "====================================="
print_eval medperf model associate -m $MOBILENET_MODEL_UID -b $BMK_UID -y
checkFailed "MobileNetV2 model association failed"
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
echo "get client certificate for data owner"
echo "====================================="
print_eval medperf certificate get_client_certificate
checkFailed "get certificate failed"
##########################################################

echo "\n"

##########################################################
echo "============================================="
echo "Submitting the certificate"
echo "============================================="
print_eval medperf certificate submit_client_certificate -y
checkFailed "Failed to submit Data Owner Certificate"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data submission step"
echo "====================================="
print_eval medperf dataset submit -p $PREP_UID -d $DIRECTORY/sample_raw_data/images -l $DIRECTORY/sample_raw_data/labels --name='cc_dataset_a' --description='cc-mock-dataset-a' --location='mock-location-a' -y
checkFailed "Data submission step failed"
DSET_UID=$(medperf dataset ls | grep cc_dataset_a | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
echo "DSET_UID=$DSET_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_UID
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_UID -y
checkFailed "Data set operational step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data association step"
echo "====================================="
print_eval medperf dataset associate -d $DSET_UID -b $BMK_UID -y
checkFailed "Data association step failed"
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
echo "Approve dataset association"
echo "====================================="
print_eval medperf association approve -b $BMK_UID -d $DSET_UID
checkFailed "Dataset association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve MobileNetV2 model association"
echo "====================================="
print_eval medperf association approve -b $BMK_UID -m $MOBILENET_MODEL_UID
checkFailed "MobileNetV2 model association approval failed"
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
echo "Configure model for CC (model owner)"
echo "====================================="
print_eval medperf confidential configure_model_for_cc -m $MOBILENET_MODEL_UID -c $MODEL_CC_CONFIG -p $MODEL_CC_POLICY
checkFailed "Model configure_for_cc failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Update model CC policy (model owner)"
echo "====================================="
print_eval medperf confidential update_model_cc_policy -m $MOBILENET_MODEL_UID
checkFailed "Model update_cc_policy failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

# echo "\n"

##########################################################
echo "====================================="
echo "Configure dataset for CC (data owner)"
echo "====================================="
print_eval medperf confidential configure_dataset_for_cc -d $DSET_UID -c $DATASET_CC_CONFIG -p $DATASET_CC_POLICY
checkFailed "Dataset configure_for_cc failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Update dataset CC policy (data owner)"
echo "====================================="
print_eval medperf confidential update_dataset_cc_policy -d $DSET_UID
checkFailed "Dataset update_cc_policy failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Setup CC operator (data owner is operator)"
echo "====================================="
print_eval medperf confidential setup_cc_operator -c $OPERATOR_CC_CONFIG
checkFailed "Setup CC operator failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Run benchmark execution (data owner is operator)"
echo "====================================="
print_eval medperf benchmark run -b $BMK_UID -d $DSET_UID
checkFailed "Benchmark execution failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Logout users"
echo "====================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

print_eval medperf auth logout
checkFailed "logout failed"

medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

medperf auth logout
checkFailed "logout failed"

medperf profile activate testdata
checkFailed "testdata profile activation failed"

medperf auth logout
checkFailed "logout failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Delete test profiles"
echo "====================================="
print_eval medperf profile activate default
checkFailed "default profile activation failed"

print_eval medperf profile delete testbenchmark
checkFailed "Profile deletion failed"

print_eval medperf profile delete testmodel
checkFailed "Profile deletion failed"

print_eval medperf profile delete testdata
checkFailed "Profile deletion failed"
##########################################################

if ${CLEANUP}; then
  clean
fi
