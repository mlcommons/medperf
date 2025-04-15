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
print_eval wget -P $DIRECTORY "$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
print_eval tar -xzvf $DIRECTORY/dataset_a.tar.gz -C $DIRECTORY
print_eval wget -P $DIRECTORY "$ASSETS_URL/assets/datasets/dataset_b.tar.gz"
print_eval tar -xzvf $DIRECTORY/dataset_b.tar.gz -C $DIRECTORY
print_eval chmod -R a+w $DIRECTORY
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
echo "Activate modelowner profile"
echo "====================================="
print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"
##########################################################

##########################################################
echo "====================================="
echo "Test auth status command"
echo "====================================="
print_eval medperf auth status
checkFailed "auth status command failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Existing cubes":
echo "====================================="
print_eval medperf mlcube ls
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

print_eval medperf mlcube submit --name mock-prep -m $PREP_MLCUBE -p $PREP_PARAMS --operational
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | grep mock-prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID"

print_eval medperf mlcube submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD --operational
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf mlcube ls | grep model1 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL1_UID=$MODEL1_UID"

print_eval medperf mlcube submit --name model2 -m $MODEL_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD --operational
checkFailed "Model2 submission failed"
MODEL2_UID=$(medperf mlcube ls | grep model2 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL2_UID=$MODEL2_UID"

# MLCube with singularity section
print_eval medperf --platform singularity mlcube submit --name model3 -m $MODEL_WITH_SINGULARITY -p $MODEL3_PARAMS -a $MODEL_ADD --operational
checkFailed "Model3 submission failed"
MODEL3_UID=$(medperf mlcube ls | grep model3 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL3_UID=$MODEL3_UID"

print_eval medperf mlcube submit --name model-fail -m $FAILING_MODEL_MLCUBE -p $MODEL4_PARAMS -a $MODEL_ADD --operational
checkFailed "failing model submission failed"
FAILING_MODEL_UID=$(medperf mlcube ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "FAILING_MODEL_UID=$FAILING_MODEL_UID"

print_eval medperf mlcube submit --name model-log-none -m $MODEL_LOG_MLCUBE -p $MODEL_LOG_NONE_PARAMS --operational
checkFailed "Model with logging None submission failed"
MODEL_LOG_NONE_UID=$(medperf mlcube ls | grep model-log-none | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL_LOG_NONE_UID=$MODEL_LOG_NONE_UID"

print_eval medperf mlcube submit --name model-log-debug -m $MODEL_LOG_MLCUBE -p $MODEL_LOG_DEBUG_PARAMS --operational
checkFailed "Model with logging debug submission failed"
MODEL_LOG_DEBUG_UID=$(medperf mlcube ls | grep model-log-debug | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL_LOG_DEBUG_UID=$MODEL_LOG_DEBUG_UID"

print_eval medperf mlcube submit --name mock-metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS --operational
checkFailed "Metrics submission failed"
METRICS_UID=$(medperf mlcube ls | grep mock-metrics | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "METRICS_UID=$METRICS_UID"
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
echo "Submit benchmark"
echo "====================================="
print_eval medperf benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-mlcube $PREP_UID --reference-model-mlcube $MODEL1_UID --evaluator-mlcube $METRICS_UID --operational
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "BMK_UID=$BMK_UID"

# Approve benchmark
echo $ADMIN
echo $MOCK_TOKENS_FILE
ADMIN_TOKEN=$(jq -r --arg ADMIN $ADMIN '.[$ADMIN]' $MOCK_TOKENS_FILE)
echo $ADMIN_TOKEN
checkFailed "Retrieving admin token failed"
print_eval "curl -sk -X PUT $SERVER_URL$VERSION_PREFIX/benchmarks/$BMK_UID/ -d '{\"approval_status\": \"APPROVED\"}' -H 'Content-Type: application/json' -H 'Authorization: Bearer $ADMIN_TOKEN' --fail-with-body"
checkFailed "Benchmark approval failed"
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
echo "Running data submission step"
echo "====================================="
print_eval "medperf dataset submit -p $PREP_UID -d $DIRECTORY/dataset_a -l $DIRECTORY/dataset_a --name='dataset_a' --description='mock dataset a' --location='mock location a' -y"
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | grep dataset_a | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
echo "DSET_A_UID=$DSET_A_UID"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_A_UID
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running exporting data while it's in development"
echo "====================================="
print_eval medperf dataset export -d $DSET_A_UID -o $TEST_ROOT/exported_dev_dataset
checkFailed "Dev Data export step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running importing development data after removing it from storage"
echo "====================================="
print_eval rm -rf $MEDPERF_STORAGE/data/$SERVER_STORAGE_ID/$DSET_A_UID
print_eval medperf dataset import -d $DSET_A_UID -i $TEST_ROOT/exported_dev_dataset/$DSET_A_UID.gz --raw_dataset_path $TEST_ROOT/imported_raw_data
checkFailed "Dev Data import step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_A_UID -y
checkFailed "Data set operational step failed"
DSET_A_GENUID=$(medperf dataset view $DSET_A_UID | grep generated_uid | cut -d " " -f 2)
echo "DSET_A_GENUID=$DSET_A_GENUID"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running exporting data while it's in operation"
echo "====================================="
print_eval medperf dataset export -d $DSET_A_UID -o $TEST_ROOT/exported_op_dataset
checkFailed "Operational Data export step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running importing operational data after removing it from storage"
echo "====================================="
print_eval rm -rf $MEDPERF_STORAGE/data/$SERVER_STORAGE_ID/$DSET_A_UID
print_eval medperf dataset import -d $DSET_A_UID -i $TEST_ROOT/exported_op_dataset/$DSET_A_UID.gz
checkFailed "Op Data import step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data association step"
echo "====================================="
print_eval medperf dataset associate -d $DSET_A_UID -b $BMK_UID -y
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
echo "Approve association"
echo "====================================="
# Mark dataset-benchmark association as approved
print_eval medperf association approve -b $BMK_UID -d $DSET_A_UID
checkFailed "Data association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model2 association"
echo "====================================="
print_eval medperf mlcube associate -m $MODEL2_UID -b $BMK_UID -y
checkFailed "Model2 association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model3 association (with singularity)"
echo "====================================="
# this will run two types of singularity mlcubes:
#   1) an already built singularity image (model 3)
#   2) a docker image to be converted (metrics)
print_eval medperf --platform singularity mlcube associate -m $MODEL3_UID -b $BMK_UID -y
checkFailed "Model3 association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Running failing model association (This will NOT fail)"
echo "======================================================"
print_eval medperf mlcube associate -m $FAILING_MODEL_UID -b $BMK_UID -y
checkFailed "Failing model association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Running logging-model-without-env association"
echo "======================================================"
print_eval medperf mlcube associate -m $MODEL_LOG_NONE_UID -b $BMK_UID -y
checkFailed "Logging-model-without-env association association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Running logging-model-with-debug association"
echo "======================================================"
print_eval medperf --container-loglevel debug mlcube associate -m $MODEL_LOG_DEBUG_UID -b $BMK_UID -y
checkFailed "Logging-model-with-debug association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Submitted associations:"
echo "======================================================"
print_eval medperf association ls
checkFailed "Listing associations failed"
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
echo "Approve model2,3,F, associations"
echo "====================================="
print_eval medperf association approve -b $BMK_UID -m $MODEL2_UID
checkFailed "Model2 association approval failed"
print_eval medperf association approve -b $BMK_UID -m $MODEL3_UID
checkFailed "Model3 association approval failed"
print_eval medperf association approve -b $BMK_UID -m $FAILING_MODEL_UID
checkFailed "failing model association approval failed"
print_eval medperf association approve -b $BMK_UID -m $MODEL_LOG_NONE_UID
checkFailed "Logging-model-without-env association approval failed"
print_eval medperf association approve -b $BMK_UID -m $MODEL_LOG_DEBUG_UID
checkFailed "Logging-model-with-debug association approval failed"
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
echo "Changing priority of model2"
echo "====================================="
print_eval medperf association set_priority -b $BMK_UID -m $MODEL2_UID -p 77
checkFailed "Priority set of model2 failed"
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
echo "Running model3 (with singularity)"
echo "====================================="
print_eval medperf --platform=singularity run -b $BMK_UID -d $DSET_A_UID -m $MODEL3_UID -y
checkFailed "Model3 run failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running outstanding models"
echo "====================================="
print_eval medperf benchmark run -b $BMK_UID -d $DSET_A_UID
checkFailed "run all outstanding models failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================================================"
echo "Run failing cube with ignore errors (This SHOULD fail since predictions folder exists)"
echo "======================================================================================"
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y --ignore-model-errors
checkSucceeded "MLCube ran successfuly but should fail since predictions folder exists"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Run failing cube with ignore errors after deleting predictions folder"
echo "====================================================================="
print_eval rm -rf $MEDPERF_STORAGE/predictions/$SERVER_STORAGE_ID/model-fail/$DSET_A_GENUID
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y --ignore-model-errors
checkFailed "Failing mlcube run with ignore errors failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running logging model without logging env"
echo "====================================="
print_eval rm -rf $MEDPERF_STORAGE/predictions/$SERVER_STORAGE_ID/model-log-none/$DSET_A_GENUID
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $MODEL_LOG_NONE_UID -y
checkFailed "run logging model without logging env failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running logging model with debug logging env"
echo "====================================="
print_eval rm -rf $MEDPERF_STORAGE/predictions/$SERVER_STORAGE_ID/model-log-debug/$DSET_A_GENUID
print_eval medperf --container-loglevel debug run -b $BMK_UID -d $DSET_A_UID -m $MODEL_LOG_DEBUG_UID -y
checkFailed "run logging model with debug logging env failed"
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
