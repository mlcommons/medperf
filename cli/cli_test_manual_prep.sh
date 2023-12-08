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

DATA_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/input_data"
LABELS_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/input_labels"

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

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

PREP_MLCUBE="https://raw.githubusercontent.com/hasan7n/medperf/0303379b00148d02e9e426076c877680bfed458f/examples/DataPrepManualSteps/data_prep/mlcube/mlcube.yaml"
PREP_PARAMS="https://raw.githubusercontent.com/hasan7n/medperf/0303379b00148d02e9e426076c877680bfed458f/examples/DataPrepManualSteps/data_prep/mlcube/workspace/parameters.yaml"
medperf mlcube submit --name manprep -m $PREP_MLCUBE -p $PREP_PARAMS
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

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
echo "Running data creation step"
echo "====================================="
medperf dataset submit -p $PREP_UID -d $DATA_PATH -l $LABELS_PATH --name="manual_a" --description="mock manual a" --location="mock location a" -y
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | grep manual_a | tr -s ' ' | cut -d ' ' -f 2)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (it will fail, needs manual steps)"
echo "====================================="
medperf dataset prepare -d $DSET_A_UID -y
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (another way)"
echo "====================================="
echo "y" | medperf dataset prepare -d $DSET_A_UID
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (another way)"
echo "====================================="
echo "n" | medperf dataset prepare -d $DSET_A_UID
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Do manual step of the preparation"
echo "====================================="
sed -i 's/0$/1/' $MEDPERF_SUBSTORAGE/data/$DSET_A_UID/data/data.csv
checkFailed "manual step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step again (this will succeed)"
echo "====================================="
medperf dataset prepare -d $DSET_A_UID -y
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data activation step"
echo "====================================="
medperf dataset activate -d $DSET_A_UID -y
checkFailed "Data activattion step failed"
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
