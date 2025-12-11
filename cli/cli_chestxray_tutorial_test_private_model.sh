# This script is meant to be called as part of cli_chestxray_tutorial_test.sh


##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"
##########################################################

echo "\n"
##########################################################
echo "============================================="
echo "Getting a certificate"
echo "============================================="
print_eval medperf certificate get_client_certificate --overwrite
checkFailed "Failed to obtain Data Owner Certificate"
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
echo "=========================================="
echo "Creating test profile for private model owner"
echo "=========================================="
print_eval medperf profile create -n testprivate
checkFailed "testprivate profile creation failed"
##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Login Private Model Owner"
echo "=========================================="

print_eval medperf profile activate testprivate
checkFailed "testprivate profile activation failed"

print_eval medperf auth logout
checkFailed "logout failed"

print_eval medperf auth login -e $PRIVATEMODELOWNER
checkFailed "testprivate login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit a private model"
echo "====================================="
print_eval medperf container submit --name privmodel \
-m $CHESTXRAY_ENCRYPTED_MODEL -p $CHESTXRAY_ENCRYPTED_MODEL_PARAMS \
-a $CHESTXRAY_ENCRYPTED_MODEL_ADD --decryption_key $PRIVATE_MODEL_LOCAL/key.bin --operational
checkFailed "private container submission failed"
PMODEL_UID=$(medperf container ls | grep privmodel | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running private model association"
echo "====================================="
print_eval medperf container associate -m $PMODEL_UID -b 1 -y
checkFailed "private model association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Give Access to Private Model"
echo "====================================="
print_eval medperf container grant_access --model-id $PMODEL_UID --benchmark-id 1 -y
checkFailed "Failed to Give Model Access to Data owner"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
print_eval medperf profile activate testdata
checkFailed "testdata profile activation failed"

print_eval medperf auth logout

print_eval medperf auth login -e $DATAOWNER
checkFailed "testdata login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running benchmark execution step - Private"
echo "====================================="
# Create results
print_eval medperf run -b 1 -d $DSET_UID -m $PMODEL_UID -y
checkFailed "Benchmark execution step failed (private)"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo " Offline Compatibility Test - Private "
echo "====================================="

## Change the server and logout just to make sure this command will work without connecting to a server
print_eval medperf profile activate noserver
checkFailed "noserver profile activation failed"

print_eval medperf test run --offline --no-cache \
--demo_dataset_url https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz \
--demo_dataset_hash "71faabd59139bee698010a0ae3a69e16d97bc4f2dde799d9e187b94ff9157c00" \
-p $PREP_LOCAL/container_config.yaml \
-m $PRIVATE_MODEL_LOCAL/container_config.yaml \
-e $METRIC_LOCAL/container_config.yaml \
-d $PRIVATE_MODEL_LOCAL/key.bin \
--data_preparator_parameters $PREP_LOCAL/workspace/parameters.yaml \
--model_parameters $MODEL_LOCAL/workspace/parameters.yaml \
--evaluator_parameters $METRIC_LOCAL/workspace/parameters.yaml \
--model_additional_files $MODEL_LOCAL/workspace/additional_files/

checkFailed "offline compatibility test execution step failed - private model"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Delete test Private Model Owner profile"
echo "====================================="
print_eval medperf profile delete testprivate
checkFailed "Profile deletion failed"
##########################################################

echo "\n"