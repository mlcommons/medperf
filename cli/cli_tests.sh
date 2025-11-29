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
print_eval medperf profile create -n testdata2
checkFailed "testdata2 profile creation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Retrieving mock datasets"
echo "====================================="
echo "downloading files to $DIRECTORY"
print_eval wget -P $DIRECTORY "$DSET_A_URL"
print_eval tar -xzvf $DIRECTORY/dataset_a.tar.gz -C $DIRECTORY
print_eval wget -P $DIRECTORY "$DSET_B_URL"
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

print_eval medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"

print_eval medperf auth login -e $DATAOWNER2
checkFailed "testdata2 login failed"
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
echo "Existing containers":
echo "====================================="
print_eval medperf container ls
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit containers"
echo "====================================="

print_eval medperf container submit --name mock-prep -m $PREP_MLCUBE -p $PREP_PARAMS --operational
checkFailed "Prep submission failed"
PREP_UID=$(medperf container ls | grep mock-prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID" >> "$LAST_ENV_FILE"

print_eval medperf container submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD --operational
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf container ls | grep model1 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL1_UID=$MODEL1_UID" >> "$LAST_ENV_FILE"

print_eval medperf container submit --name model2 -m $MODEL_ARCHIVE_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD --operational
checkFailed "Model2 submission failed"
MODEL2_UID=$(medperf container ls | grep model2 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL2_UID=$MODEL2_UID" >> "$LAST_ENV_FILE"

# Container with singularity section
print_eval medperf --platform singularity container submit --name model3 -m $MODEL_WITH_SINGULARITY -p $MODEL3_PARAMS -a $MODEL_ADD --operational
checkFailed "Model3 submission failed"
MODEL3_UID=$(medperf container ls | grep model3 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL3_UID=$MODEL3_UID" >> "$LAST_ENV_FILE"

print_eval medperf container submit --name model-fail -m $FAILING_MODEL_MLCUBE -p $MODEL4_PARAMS -a $MODEL_ADD --operational
checkFailed "failing model submission failed"
FAILING_MODEL_UID=$(medperf container ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "FAILING_MODEL_UID=$FAILING_MODEL_UID" >> "$LAST_ENV_FILE"

print_eval medperf container submit --name mock-metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS --operational
checkFailed "Metrics submission failed"
METRICS_UID=$(medperf container ls | grep mock-metrics | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "METRICS_UID=$METRICS_UID" >> "$LAST_ENV_FILE"
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
print_eval medperf benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-container $PREP_UID --reference-model-container $MODEL1_UID --evaluator-container $METRICS_UID --operational
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "BMK_UID=$BMK_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Update benchmark association approval policy"
echo "====================================="
# create the allowlist file with only the data owner
echo "$DATAOWNER" >>$DIRECTORY/allowlist.txt
print_eval medperf benchmark update_associations_policy -b $BMK_UID --dataset_auto_approve_mode allowlist --dataset_auto_approve_file $DIRECTORY/allowlist.txt
checkFailed "benchmark update policy failed"
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
echo "DSET_A_UID=$DSET_A_UID" >> "$LAST_ENV_FILE"
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
echo "DSET_A_GENUID=$DSET_A_GENUID" >> "$LAST_ENV_FILE"
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
echo "Activate dataowner2 profile"
echo "====================================="
print_eval medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data submission step"
echo "====================================="
print_eval "medperf dataset submit -p $PREP_UID -d $DIRECTORY/dataset_b -l $DIRECTORY/dataset_b --name='dataset_b' --description='mock dataset b' --location='mock location b' -y"
checkFailed "Data2 submission step failed"
DSET_B_UID=$(medperf dataset ls | grep dataset_b | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
echo "DSET_B_UID=$DSET_B_UID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data2 preparation step"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_B_UID
checkFailed "Data2 preparation step failed"
##########################################################

echo "\n"
##########################################################
echo "====================================="
echo "Running data2 set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_B_UID -y
checkFailed "Data2 set operational step failed"
DSET_B_GENUID=$(medperf dataset view $DSET_B_UID | grep generated_uid | cut -d " " -f 2)
echo "DSET_B_GENUID=$DSET_B_GENUID" >> "$LAST_ENV_FILE"
##########################################################

echo "\n"
##########################################################
echo "====================================="
echo "Running data2 association step"
echo "====================================="
print_eval medperf dataset associate -d $DSET_B_UID -b $BMK_UID -y
checkFailed "Data2 association step failed"
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
echo "Approve data association. This will fail because it's auto-approved"
echo "====================================="
# Mark dataset-benchmark association as approved
print_eval medperf association approve -b $BMK_UID -d $DSET_A_UID
checkSucceeded "Data association approval should fail, but it succeeded"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve data2 association"
echo "====================================="
# Mark dataset-benchmark association as approved
print_eval medperf association approve -b $BMK_UID -d $DSET_B_UID
checkFailed "Data2 association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model2 association"
echo "====================================="
print_eval medperf container associate -m $MODEL2_UID -b $BMK_UID -y
checkFailed "Model2 association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model3 association (with singularity)"
echo "====================================="
# this will run two types of singularity containers:
#   1) an already built singularity image (model 3)
#   2) a docker image to be converted (metrics)
print_eval medperf --platform singularity container associate -m $MODEL3_UID -b $BMK_UID -y
checkFailed "Model3 association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Running failing model association (This will NOT fail)"
echo "======================================================"
print_eval medperf container associate -m $FAILING_MODEL_UID -b $BMK_UID -y
checkFailed "Failing model association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Submitted associations:"
echo "======================================================"
print_eval medperf association ls -bd
checkFailed "Listing benchmark-datasets associations failed"
print_eval medperf association ls -bm
checkFailed "Listing benchmark-models associations failed"
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
echo "====================================================================="
echo "Run failing container with ignore errors"
echo "====================================================================="
print_eval medperf result create -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID --ignore-model-errors
checkFailed "Failing container run with ignore errors failed"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "View local result"
echo "====================================================================="
FAILING_MODEL_RESULT_ID=$(medperf result ls --mine | grep b${BMK_UID}m${FAILING_MODEL_UID}d${DSET_A_UID} | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
echo "FAILING_MODEL_RESULT_ID=$FAILING_MODEL_RESULT_ID" >> "$LAST_ENV_FILE"
print_eval medperf result show_local_results $FAILING_MODEL_RESULT_ID
checkFailed "show_local_results failed"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Submit failing container's result"
echo "====================================================================="
print_eval medperf result submit -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y
checkFailed "Failing container run with ignore errors failed"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Rerun (execute+submit). This will error out"
echo "====================================================================="
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID --ignore-model-errors -y
checkSucceeded "Rerunning should fail, but it succeeded"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Rerun (execute+submit) with --new-result flag. This should work."
echo "====================================================================="
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID --ignore-model-errors --new-result -y
checkFailed "Rerunning with --new-result failed"
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

medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"

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

print_eval medperf profile delete testdata2
checkFailed "Profile deletion failed"
##########################################################

if ${CLEANUP}; then
  clean
fi
