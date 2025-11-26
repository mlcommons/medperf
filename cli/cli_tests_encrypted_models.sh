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

echo "\n"

##########################################################
echo "====================================="
echo "Submit containers"
echo "====================================="

print_eval medperf container submit --name mock-prep -m $PREP_MLCUBE -p $PREP_PARAMS --operational
checkFailed "Prep submission failed"
PREP_UID=$(medperf container ls | grep mock-prep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "PREP_UID=$PREP_UID"

# Public model docker archive
print_eval medperf container submit --name model1 -m $MODEL_ARCHIVE_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD --operational
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf container ls | grep model1 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL1_UID=$MODEL1_UID"

# Encrypted model docker archive
print_eval medperf container submit --name model2 -m $MODEL_ENCRYPTED_ARCHIVE_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD --decryption-key $DOCKER_DECRYPTION_KEY --operational
checkFailed "Model2 submission failed"
MODEL2_UID=$(medperf container ls | grep model2 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL2_UID=$MODEL2_UID"

# Encrypted model singularity file
print_eval medperf --platform singularity container submit --name model3 -m $MODEL_ENCRYPTED_SINGULARITY_MLCUBE -p $MODEL3_PARAMS -a $MODEL_ADD --decryption-key $SINGULARITY_DECRYPTION_KEY --operational
checkFailed "Model3 submission failed"
MODEL3_UID=$(medperf container ls | grep model3 | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "MODEL3_UID=$MODEL3_UID"

print_eval medperf container submit --name mock-metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS --operational
checkFailed "Metrics submission failed"
METRICS_UID=$(medperf container ls | grep mock-metrics | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
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
echo "Submit benchmark (using singularity to test conversion of docker archive during compatibility test)"
echo "====================================="
print_eval medperf --platform singularity benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-container $PREP_UID --reference-model-container $MODEL1_UID --evaluator-container $METRICS_UID --operational
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | grep bmk | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "BMK_UID=$BMK_UID"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Update benchmark association approval policy"
echo "====================================="
# create the allowlist file with only the data owner
echo "$DATAOWNER" >>$DIRECTORY/allowlist.txt
echo "$DATAOWNER2" >>$DIRECTORY/allowlist.txt
print_eval medperf benchmark update_associations_policy -b $BMK_UID --dataset_auto_approve_mode allowlist --dataset_auto_approve_file $DIRECTORY/allowlist.txt --model_auto_approve_mode always
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
checkFailed "Data set operational step failed"
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
echo "============================================="
echo "Getting a certificate (dataowner1)"
echo "============================================="
print_eval medperf certificate get_client_certificate
checkFailed "Failed to obtain Data Owner1 Certificate"
##########################################################

echo "\n"

##########################################################
echo "============================================="
echo "Submitting the certificate (dataowner1)"
echo "============================================="
print_eval medperf certificate submit_client_certificate -y
checkFailed "Failed to submit Data Owner1 Certificate"
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
echo "DSET_B_UID=$DSET_B_UID"
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
echo "============================================="
echo "Getting a certificate (dataowner2)"
echo "============================================="
print_eval medperf certificate get_client_certificate
checkFailed "Failed to obtain Data Owner2 Certificate"
##########################################################

echo "\n"

##########################################################
echo "============================================="
echo "Submitting the certificate (dataowner2)"
echo "============================================="
print_eval medperf certificate submit_client_certificate -y
checkFailed "Failed to submit Data Owner2 Certificate"
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
echo "Running model2 association (with singularity)"
echo "====================================="
print_eval medperf --platform singularity container associate -m $MODEL2_UID -b $BMK_UID -y
checkFailed "Model2 association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model3 association (with singularity)"
echo "====================================="
print_eval medperf --platform singularity container associate -m $MODEL3_UID -b $BMK_UID -y
checkFailed "Model3 association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Giving access to model 2"
echo "====================================="
print_eval medperf container grant_access --model-id $MODEL2_UID --benchmark-id $BMK_UID -y
checkFailed "Model2 giving access failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Giving access to model 3 with filtering"
echo "====================================="
print_eval medperf container grant_access --model-id $MODEL3_UID --benchmark-id $BMK_UID --allowed_emails "$DATAOWNER" -y
checkFailed "Model2 giving access failed"
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
echo "Running model2"
echo "====================================="
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $MODEL2_UID -y
checkFailed "Model2 run failed"
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
echo "Activate dataowner2 profile"
echo "====================================="
print_eval medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model3 (This should fail since access is not granted yet)"
echo "====================================="
print_eval medperf --platform=singularity run -b $BMK_UID -d $DSET_B_UID -m $MODEL3_UID -y
checkSucceeded "Model3 run should fail"
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
echo "Giving access to model 3 for data owner2"
echo "====================================="
print_eval medperf container grant_access --model-id $MODEL3_UID --benchmark-id $BMK_UID -y
checkFailed "Model3 giving access failed"
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
echo "Running outstanding models"
echo "====================================="
print_eval medperf --platform singularity benchmark run -b $BMK_UID -d $DSET_B_UID
checkFailed "run all outstanding models failed"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Submit model2 result"
echo "====================================================================="
print_eval medperf result submit -b $BMK_UID -d $DSET_B_UID -m $MODEL2_UID -y
checkFailed "model2 result submission failed"
##########################################################

echo "\n"

##########################################################
echo "====================================================================="
echo "Submit model3 result"
echo "====================================================================="
print_eval medperf result submit -b $BMK_UID -d $DSET_B_UID -m $MODEL3_UID -y
checkFailed "model3 result submission failed"
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
echo "Removing access for data owner1"
echo "====================================="
print_eval medperf container revoke_user_access -k 3 -y
checkFailed "Model3 revoke access failed"
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
echo "Running model3 (This should fail since access was revoked)"
echo "====================================="
print_eval medperf run -b $BMK_UID -d $DSET_A_UID -m $MODEL3_UID --no-cache --new-result -y
checkSucceeded "Model3 run should fail"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Checking access to model3"
# This will return zero status code if "denied" was in the output
print_eval medperf container check_access -c $MODEL3_UID | grep -iq "denied"
checkFailed "check access command should print access denied"
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
echo "Give back access"
echo "====================================="
print_eval medperf container grant_access --model-id $MODEL3_UID --benchmark-id $BMK_UID -y
checkFailed "Model3 giving access failed"
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
echo "Checking access to model3"
# This will return zero status code if "denied" was in the output
print_eval medperf container check_access -c $MODEL3_UID | grep -iq "denied"
checkSucceeded "check access command should not print access denied"
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
echo "Delete all keys of model 3"
echo "====================================="
print_eval medperf container delete_keys --container-id $MODEL3_UID -y
checkFailed "Model3 giving access failed"
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
echo "Checking access to model3"
# This will return zero status code if "denied" was in the output
print_eval medperf container check_access -c $MODEL3_UID | grep -iq "denied"
checkFailed "check access command should print access denied"
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
echo "Checking access to model3"
# This will return zero status code if "denied" was in the output
print_eval medperf container check_access -c $MODEL3_UID | grep -iq "denied"
checkFailed "check access command should print access denied"
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
