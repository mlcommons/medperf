# import setup
. "$(dirname $(realpath "$0"))/tests_setup.sh"

##########################################################
################### Start Testing ########################
##########################################################


##########################################################
echo "=========================================="
echo "Printing MedPerf version"
echo "=========================================="
medperf --version
checkFailed "MedPerf version failed"
##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Creating test profiles for each user"
echo "=========================================="
medperf profile activate local
checkFailed "local profile creation failed"

medperf profile create -n testbenchmark
checkFailed "testbenchmark profile creation failed"
medperf profile create -n testmodel
checkFailed "testmodel profile creation failed"
medperf profile create -n testdata
checkFailed "testdata profile creation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Retrieving mock datasets"
echo "====================================="
echo "downloading files to $DIRECTORY"
wget -P $DIRECTORY "$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
tar -xzvf $DIRECTORY/dataset_a.tar.gz -C $DIRECTORY
wget -P $DIRECTORY "$ASSETS_URL/assets/datasets/dataset_b.tar.gz"
tar -xzvf $DIRECTORY/dataset_b.tar.gz -C $DIRECTORY
chmod -R a+w $DIRECTORY
##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Login each user"
echo "=========================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

medperf auth login -e $BENCHMARKOWNER
checkFailed "testbenchmark login failed"

medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

medperf auth login -e $MODELOWNER
checkFailed "testmodel login failed"

medperf profile activate testdata
checkFailed "testdata profile activation failed"

medperf auth login -e $DATAOWNER
checkFailed "testdata login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate modelowner profile"
echo "====================================="
medperf profile activate testmodel
checkFailed "testmodel profile activation failed"
##########################################################

##########################################################
echo "====================================="
echo "Test auth status command"
echo "====================================="
medperf auth status
checkFailed "auth status command failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "existing cubes":
echo "====================================="
medperf mlcube ls
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

medperf mlcube submit --name prep -m $PREP_MLCUBE -p $PREP_PARAMS
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | grep prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf mlcube ls | grep model1 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model2 -m $MODEL_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD
checkFailed "Model2 submission failed"
MODEL2_UID=$(medperf mlcube ls | grep model2 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

# MLCube with singularity section
medperf mlcube submit --name model3 -m $MODEL_WITH_SINGULARITY -p $MODEL3_PARAMS -a $MODEL_ADD -i $MODEL_SING_IMAGE
checkFailed "Model3 submission failed"
MODEL3_UID=$(medperf mlcube ls | grep model3 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model-fail -m $FAILING_MODEL_MLCUBE -p $MODEL4_PARAMS -a $MODEL_ADD
checkFailed "failing model submission failed"
FAILING_MODEL_UID=$(medperf mlcube ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model-log-none -m $MODEL_LOG_MLCUBE -p $MODEL_LOG_NONE_PARAMS
checkFailed "Model with logging None submission failed"
MODEL_LOG_NONE_UID=$(medperf mlcube ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model-log-debug -m $MODEL_LOG_MLCUBE -p $MODEL_LOG_DEBUG_PARAMS
checkFailed "Model with logging debug submission failed"
MODEL_LOG_DEBUG_UID=$(medperf mlcube ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS
checkFailed "Metrics submission failed"
METRICS_UID=$(medperf mlcube ls | grep model-fail | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate benchmarkowner profile"
echo "====================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit benchmark"
echo "====================================="
medperf benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-mlcube $PREP_UID --reference-model-mlcube $MODEL1_UID --evaluator-mlcube $METRICS_UID
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

# Approve benchmark
ADMIN_TOKEN=$(jq -r --arg ADMIN $ADMIN '.[$ADMIN]' $MOCK_TOKENS_FILE)
checkFailed "Retrieving admin token failed"
curl -sk -X PUT $SERVER_URL$VERSION_PREFIX/benchmarks/$BMK_UID/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Bearer $ADMIN_TOKEN"
checkFailed "Benchmark approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf dataset create -p $PREP_UID -d $DIRECTORY/dataset_a -l $DIRECTORY/dataset_a --name="dataset_a" --description="mock dataset a" --location="mock location a"
checkFailed "Data preparation step failed"
DSET_A_GENUID=$(medperf dataset ls | grep dataset_a | tr -s ' ' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data submission step"
echo "====================================="
medperf dataset submit -d $DSET_A_GENUID -y
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | grep dataset_a | tr -s ' ' | cut -d ' ' -f 1)
##########################################################

echo "\n"


##########################################################
echo "====================================="
echo "Moving storage to some other location"
echo "====================================="
medperf storage move -t /tmp/some_folder
checkFailed "moving storage failed"
MEDPERF_STORAGE="/tmp/some_folder/.medperf"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data association step"
echo "====================================="
medperf dataset associate -d $DSET_A_UID -b $BMK_UID -y
checkFailed "Data association step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate benchmarkowner profile"
echo "====================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve association"
echo "====================================="
# Mark dataset-benchmark association as approved
medperf association approve -b $BMK_UID -d $DSET_A_UID
checkFailed "Data association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model2 association"
echo "====================================="
medperf mlcube associate -m $MODEL2_UID -b $BMK_UID -y
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
medperf --platform singularity mlcube associate -m $MODEL3_UID -b $BMK_UID -y
checkFailed "Model3 association failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================"
echo "Running failing model association (This will NOT fail)"
echo "======================================================"
medperf mlcube associate -m $FAILING_MODEL_UID -b $BMK_UID -y
checkFailed "Failing model association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate modelowner profile"
echo "====================================="
medperf profile activate testmodel
checkFailed "testmodel profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve model2,3,F, associations"
echo "====================================="
medperf association approve -b $BMK_UID -m $MODEL2_UID
checkFailed "Model2 association approval failed"
medperf association approve -b $BMK_UID -m $MODEL3_UID
checkFailed "Model3 association approval failed"
medperf association approve -b $BMK_UID -m $FAILING_MODEL_UID
checkFailed "failing model association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate benchmarkowner profile"
echo "====================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Changing priority of model2"
echo "====================================="
medperf association set_priority -b $BMK_UID -m $MODEL2_UID -p 77
checkFailed "Priority set of model2 failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model3 (with singularity)"
echo "====================================="
medperf --platform=singularity run -b $BMK_UID -d $DSET_A_UID -m $MODEL3_UID -y
checkFailed "Model3 run failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running outstanding models"
echo "====================================="
medperf benchmark run -b $BMK_UID -d $DSET_A_UID
checkFailed "run all outstanding models failed"
##########################################################

echo "\n"

##########################################################
echo "======================================================================================"
echo "Run failing cube with ignore errors (This SHOULD fail since predictions folder exists)"
echo "======================================================================================"
medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y --ignore-model-errors
if [ "$?" -eq 0 ]; then
  i_am_a_command_that_does_not_exist_and_hence_changes_the_last_exit_status_to_nonzero
fi
checkFailed "MLCube ran successfuly but should fail since predictions folder exists"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Run failing cube with ignore errors after deleting predictions folder"
echo "====================================================================="
rm -rf $MEDPERF_STORAGE/predictions/$SERVER_STORAGE_ID/model-fail/$DSET_A_GENUID
medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y --ignore-model-errors
checkFailed "Failing mlcube run with ignore errors failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running logging model without logging env"
echo "====================================="
medperf benchmark run -b $BMK_UID -d $DSET_A_UID -m $MODEL_LOG_NONE_UID
checkFailed "run logging model without logging env failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running logging model with debug logging env"
echo "====================================="
# TODO: this MUST fail for now
medperf benchmark run -b $BMK_UID -d $DSET_A_UID -m $MODEL_LOG_DEBUG_UID
checkFailed "run logging model with debug logging env failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Logout users"
echo "====================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

medperf auth logout
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
medperf profile activate default
checkFailed "default profile activation failed"

medperf profile delete testbenchmark
checkFailed "Profile deletion failed"

medperf profile delete testmodel
checkFailed "Profile deletion failed"

medperf profile delete testdata
checkFailed "Profile deletion failed"
##########################################################

if ${CLEANUP}; then
  clean
fi
