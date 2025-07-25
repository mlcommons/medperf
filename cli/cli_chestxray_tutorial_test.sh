# import setup
. "$(dirname $(realpath "$0"))/tests_setup.sh"

##########################################################
################### Start Testing ########################
##########################################################

echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
echo "downloading files to $DIRECTORY"
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_raw_data.tar.gz
tar -xzvf $DIRECTORY/sample_raw_data.tar.gz -C $DIRECTORY
chmod a+w $DIRECTORY/sample_raw_data

##########################################################

echo "=========================================="
echo "Creating test profiles for each user"
echo "=========================================="
print_eval medperf profile activate local
checkFailed "local profile creation failed"

print_eval medperf profile create -n testbenchmark
checkFailed "testbenchmark profile creation failed"
print_eval medperf profile create -n testdata
checkFailed "testdata profile creation failed"
print_eval medperf profile create -n noserver
checkFailed "noserver profile creation failed"
print_eval medperf profile set --server https://example.com
checkFailed "setting mock server failed"

echo "=========================================="
echo "Login each user"
echo "=========================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

print_eval medperf auth login -e $BENCHMARKOWNER
checkFailed "testbenchmark login failed"

print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf auth login -e $DATAOWNER
checkFailed "testdata login failed"

echo "====================================="
echo ""Activate benchmarkowner profile""
echo "====================================="
# Log in as the benchmark owner
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

echo "====================================="
echo ""Change association approval policy to auto approve always""
echo "====================================="
# Log in as the benchmark owner
print_eval medperf benchmark update_associations_policy -b 1 --dataset_auto_approve_mode ALWAYS
checkFailed "benchmark update policy failed"

echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"
echo "\n"
echo "====================================="
echo "Registering dataset with medperf"
echo "====================================="
print_eval "medperf dataset submit -b 1 -d $DIRECTORY/sample_raw_data/images -l $DIRECTORY/sample_raw_data/labels --name='nih_chestxray' --description='sample dataset' --location='mock location' -y"
checkFailed "Data registration step failed"

echo "\n"
DSET_UID=$(medperf dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "Dataset UID: $DSET_UID"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
print_eval medperf dataset prepare -d $DSET_UID
checkFailed "Data preparation step failed"

echo "\n"

echo "====================================="
echo "Running data set operational step"
echo "====================================="
print_eval medperf dataset set_operational -d $DSET_UID -y
checkFailed "Data set operational step failed"

echo "====================================="
echo "Creating dataset benchmark association"
echo "====================================="
print_eval medperf dataset associate -d $DSET_UID -b 1 -y
checkFailed "Data association step failed"

echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
# Create results
print_eval medperf run -b 1 -d $DSET_UID -m 5 -y
checkFailed "Benchmark execution step failed"

# Test offline compatibility test
print_eval wget -P $MODEL_LOCAL/workspace/additional_files "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz"
print_eval tar -xzvf $MODEL_LOCAL/workspace/additional_files/cnn_weights.tar.gz -C $MODEL_LOCAL/workspace/additional_files

## Change the server and logout just to make sure this command will work without connecting to a server
print_eval medperf profile activate noserver
checkFailed "noserver profile activation failed"

print_eval medperf test run --offline --no-cache \
  --demo_dataset_url https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz \
  --demo_dataset_hash "71faabd59139bee698010a0ae3a69e16d97bc4f2dde799d9e187b94ff9157c00" \
  -p $PREP_LOCAL/container_config.yaml \
  -m $MODEL_LOCAL/container_config.yaml \
  -e $METRIC_LOCAL/container_config.yaml

checkFailed "offline compatibility test execution step failed"
print_eval rm $MODEL_LOCAL/workspace/additional_files/cnn_weights.tar.gz
print_eval rm $MODEL_LOCAL/workspace/additional_files/cnn_weights.pth

echo "====================================="
echo "Logout users"
echo "====================================="
print_eval medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

print_eval medperf auth logout
checkFailed "logout failed"

print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf auth logout
checkFailed "logout failed"

echo "====================================="
echo "Delete test profiles"
echo "====================================="
print_eval medperf profile activate default
checkFailed "default profile activation failed"

print_eval medperf profile delete testbenchmark
checkFailed "Profile deletion failed"

print_eval medperf profile delete testdata
checkFailed "Profile deletion failed"

print_eval medperf profile delete noserver
checkFailed "Profile deletion failed"

if ${CLEANUP}; then
  clean
fi
