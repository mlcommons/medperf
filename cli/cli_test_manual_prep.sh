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

DATA_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/input_data"
LABELS_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/input_labels"

PREPARED_DATA_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/prepared_data_example/data"
PREPARED_LABELS_PATH="$(dirname $(dirname $(realpath "$0")))/examples/DataPrepManualSteps/data_prep/mlcube/workspace/prepared_data_example/labels"
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

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

PREP_MLCUBE="https://raw.githubusercontent.com/aristizabal95/medperf-2/4aea7de62fd71b377fd3a0b58352d104fd8f9c08/examples/DataPrepManualSteps/data_prep/mlcube/mlcube.yaml"
PREP_PARAMS="https://raw.githubusercontent.com/aristizabal95/medperf-2/4aea7de62fd71b377fd3a0b58352d104fd8f9c08/examples/DataPrepManualSteps/data_prep/mlcube/workspace/parameters.yaml"
print_eval medperf mlcube submit --name manprep -m $PREP_MLCUBE -p $PREP_PARAMS
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID"

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
echo "Running data creation step"
echo "====================================="
print_eval "medperf dataset submit -p $PREP_UID -d $DATA_PATH -l $LABELS_PATH --name='manual_a' --description='mock manual a' --location='mock location a' -y"
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | grep manual_a | tr -s ' ' | cut -d ' ' -f 2)
echo "DSET_A_UID=$DSET_A_UID"

##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (it will fail, needs manual steps)"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_A_UID -y
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (another way)"
echo "====================================="
print_eval echo "y" | medperf dataset prepare -d $DSET_A_UID
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step (another way)"
echo "====================================="
print_eval echo "n" | medperf dataset prepare -d $DSET_A_UID
checkSucceeded "Data preparation step should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Do manual step of the preparation"
echo "====================================="
print_eval "sed -i 's/0$/1/' $MEDPERF_STORAGE/data/$SERVER_STORAGE_ID/$DSET_A_UID/data/data.csv"
checkFailed "manual step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step again (this will succeed)"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_A_UID -y
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_A_UID -y
checkFailed "Data activattion step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data creation step"
echo "====================================="
print_eval "medperf dataset submit -p $PREP_UID -d $PREPARED_DATA_PATH -l $PREPARED_LABELS_PATH --name='already_a' --description='mock already a' --location='mock location a' -y --submit-as-prepared"
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | grep already_a | tr -s ' ' | cut -d ' ' -f 2)
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
echo "Running data set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_A_UID -y
checkFailed "Data activattion step failed"
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

print_eval medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

print_eval medperf auth logout
checkFailed "logout failed"

print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf auth logout
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
