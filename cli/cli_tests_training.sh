# import setup
. "$(dirname $(realpath "$0"))/tests_setup.sh"

##########################################################
################### Start Testing ########################
##########################################################

##########################################################
echo "=========================================="
echo "Creating test profiles for each user"
echo "=========================================="
medperf profile activate local
checkFailed "local profile creation failed"

medperf profile create -n testmodel
checkFailed "testmodel profile creation failed"
medperf profile create -n testagg
checkFailed "testagg profile creation failed"
medperf profile create -n testdata1
checkFailed "testdata1 profile creation failed"
medperf profile create -n testdata2
checkFailed "testdata2 profile creation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Retrieving mock datasets"
echo "====================================="
echo "downloading files to $DIRECTORY"

wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/testfl/data/col1.tar.gz
tar -xf $DIRECTORY/col1.tar.gz -C $DIRECTORY
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/testfl/data/col2.tar.gz
tar -xf $DIRECTORY/col2.tar.gz -C $DIRECTORY
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/testfl/data/test.tar.gz
tar -xf $DIRECTORY/test.tar.gz -C $DIRECTORY
rm $DIRECTORY/col1.tar.gz
rm $DIRECTORY/col2.tar.gz
rm $DIRECTORY/test.tar.gz

##########################################################

echo "\n"

##########################################################
echo "=========================================="
echo "Login each user"
echo "=========================================="
medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

medperf auth login -e $MODELOWNER
checkFailed "testmodel login failed"

medperf profile activate testagg
checkFailed "testagg profile activation failed"

medperf auth login -e $AGGOWNER
checkFailed "testagg login failed"

medperf profile activate testdata1
checkFailed "testdata1 profile activation failed"

medperf auth login -e $DATAOWNER
checkFailed "testdata1 login failed"

medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"

medperf auth login -e $DATAOWNER2
checkFailed "testdata2 login failed"
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

medperf mlcube submit --name trainprep -m $PREP_TRAINING_MLCUBE
checkFailed "Train prep submission failed"
PREP_UID=$(medperf mlcube ls | grep trainprep | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name traincube -m $TRAIN_MLCUBE -p $TRAIN_PARAMS -a $TRAIN_WEIGHTS
checkFailed "traincube submission failed"
TRAINCUBE_UID=$(medperf mlcube ls | grep traincube | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit Training Experiment"
echo "====================================="
medperf training submit -n trainexp -d trainexp -p $PREP_UID -m $TRAINCUBE_UID
checkFailed "Training exp submission failed"
TRAINING_UID=$(medperf training ls | grep trainexp | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

# Approve benchmark
ADMIN_TOKEN=$(jq -r --arg ADMIN $ADMIN '.[$ADMIN]' $MOCK_TOKENS_FILE)
checkFailed "Retrieving admin token failed"
curl -sk -X PUT $SERVER_URL$VERSION_PREFIX/training/$TRAINING_UID/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Bearer $ADMIN_TOKEN"
checkFailed "training exp approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate aggowner profile"
echo "====================================="
medperf profile activate testagg
checkFailed "testagg profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running aggregator submission step"
echo "====================================="
HOSTNAME_=$(hostname -A | cut -d " " -f 1)
medperf aggregator submit -n aggreg -a $HOSTNAME_ -p 50273
checkFailed "aggregator submission step failed"
AGG_UID=$(medperf aggregator ls | grep aggreg | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running aggregator association step"
echo "====================================="
medperf aggregator associate -a $AGG_UID -t $TRAINING_UID -y
checkFailed "aggregator association step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
medperf profile activate testdata1
checkFailed "testdata1 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data1 preparation step"
echo "====================================="
medperf dataset create -p $PREP_UID -d $DIRECTORY/col1 -l $DIRECTORY/col1 --name="col1" --description="col1data" --location="col1location"
checkFailed "Data1 preparation step failed"
DSET_1_GENUID=$(medperf dataset ls | grep col1 | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data1 submission step"
echo "====================================="
medperf dataset submit -d $DSET_1_GENUID -y
checkFailed "Data1 submission step failed"
DSET_1_UID=$(medperf dataset ls | grep col1 | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data1 association step"
echo "====================================="
medperf training associate_dataset -d $DSET_1_UID -t $TRAINING_UID -y
checkFailed "Data1 association step failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner2 profile"
echo "====================================="
medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data2 preparation step"
echo "====================================="
medperf dataset create -p $PREP_UID -d $DIRECTORY/col2 -l $DIRECTORY/col2 --name="col2" --description="col2data" --location="col2location"
checkFailed "Data2 preparation step failed"
DSET_2_GENUID=$(medperf dataset ls | grep col2 | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data2 submission step"
echo "====================================="
medperf dataset submit -d $DSET_2_GENUID -y
checkFailed "Data2 submission step failed"
DSET_2_UID=$(medperf dataset ls | grep col2 | tr -s ' ' | awk '{$1=$1;print}' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data2 association step"
echo "====================================="
medperf training associate_dataset -d $DSET_2_UID -t $TRAINING_UID -y
checkFailed "Data2 association step failed"
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
echo "Approve aggregator association"
echo "====================================="
medperf training approve_association -t $TRAINING_UID -a $AGG_UID
checkFailed "agg association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve data1 association"
echo "====================================="
medperf training approve_association -t $TRAINING_UID -d $DSET_1_UID
checkFailed "data1 association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Approve data2 association"
echo "====================================="
medperf training approve_association -t $TRAINING_UID -d $DSET_2_UID
checkFailed "data2 association approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Lock experiment"
echo "====================================="
medperf training lock -t $TRAINING_UID
checkFailed "locking experiment failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate aggowner profile"
echo "====================================="
medperf profile activate testagg
checkFailed "testagg profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Starting aggregator"
echo "====================================="
RUNCOMMAND="medperf aggregator start -a $AGG_UID -t $TRAINING_UID"
nohup $RUNCOMMAND </dev/null &>agg.log &

# sleep so that the mlcube is run before we change profiles
sleep 7

AGG_PID=$(ps -ef | grep "$RUNCOMMAND" | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
# Check if the command is still running.
if ! kill -0 "$AGG_PID" &>/dev/null; then
  checkFailed "agg doesn't seem to be running" 1
fi
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
medperf profile activate testdata1
checkFailed "testdata1 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Starting training with data1"
echo "====================================="
RUNCOMMAND="medperf training run -d $DSET_1_UID -t $TRAINING_UID"
nohup $RUNCOMMAND </dev/null &>col1.log &

# sleep so that the mlcube is run before we change profiles
sleep 7

DATA1_PID=$(ps -ef | grep "$RUNCOMMAND" | head -n 1 | tr -s ' ' | cut -d ' ' -f 2)
# Check if the command is still running.
if ! kill -0 "$DATA1_PID" &>/dev/null; then
  checkFailed "data1 training doesn't seem to be running" 1
fi
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Activate dataowner2 profile"
echo "====================================="
medperf profile activate testdata2
checkFailed "testdata2 profile activation failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Starting training with data2"
echo "====================================="
medperf training run -d $DSET_2_UID -t $TRAINING_UID
checkFailed "data2 training failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Waiting for other prcocesses to exit successfully"
echo "====================================="
# NOTE: on systems with small process ID table or very short-lived processes,
#       there is a probability that PIDs are reused and hence the
#       code below may be inaccurate. Perhaps grep processes according to command
#       string is the most efficient way to reduce that probability further.
# Followup NOTE: not sure, but the "wait" command may fail if it is waiting for
#                a process that is not a child of the current shell
wait $DATA1_PID
checkFailed "data1 training didn't exit successfully"
wait $AGG_PID
checkFailed "aggregator didn't exit successfully"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Logout users"
echo "====================================="
medperf profile activate testmodel
checkFailed "testmodel profile activation failed"

medperf auth logout
checkFailed "logout failed"

medperf profile activate testagg
checkFailed "testagg profile activation failed"

medperf auth logout
checkFailed "logout failed"

medperf profile activate testdata1
checkFailed "testdata1 profile activation failed"

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
medperf profile activate default
checkFailed "default profile activation failed"

medperf profile delete testmodel
checkFailed "Profile deletion failed"

medperf profile delete testagg
checkFailed "Profile deletion failed"

medperf profile delete testdata1
checkFailed "Profile deletion failed"

medperf profile delete testdata2
checkFailed "Profile deletion failed"
##########################################################

if ${CLEANUP}; then
  clean
fi
