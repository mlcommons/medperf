#! /bin/bash
while getopts s:d:c:a:f flag
do
    case "${flag}" in
        s) SERVER_URL=${OPTARG};;
        d) DIRECTORY=${OPTARG};;
        c) CLEANUP="true";;
        a) AUTH_CERT=${OPTARG};;
        f) FRESH="true";;
    esac
done

SERVER_URL="${SERVER_URL:-https://127.0.0.1:8000}"
DIRECTORY="${DIRECTORY:-/tmp/medperf_test_files}"
CLEANUP="${CLEANUP:-false}"
FRESH="${FRESH:-false}"
CERT_FILE="${AUTH_CERT:-$(realpath server/cert.crt)}"
MEDPERF_STORAGE=~/.medperf
MEDPERF_SUBSTORAGE="$MEDPERF_STORAGE/$(echo $SERVER_URL | cut -d '/' -f 3 | sed -e 's/[.:]/_/g')"
MEDPERF_LOG_STORAGE="$MEDPERF_SUBSTORAGE/logs/medperf.log"

echo "Server URL: $SERVER_URL"
echo "Storage location: $MEDPERF_SUBSTORAGE"
echo "Certificate: $CERT_FILE"

# frequently used
clean(){
  echo "====================================="
  echo "Cleaning up medperf tmp files"
  echo "====================================="
  rm -fr $DIRECTORY
  rm -fr $MEDPERF_SUBSTORAGE
  # errors of the commands below are ignored
  medperf profile activate default
  medperf profile delete mocktest
}
checkFailed(){
  if [ "$?" -ne "0" ]; then
    echo $1
    tail "$MEDPERF_LOG_STORAGE"
    if ${CLEANUP}; then
      clean
    fi
    exit 1
  fi
}


if ${FRESH}; then
  clean
fi
##########################################################
########################## Setup #########################
##########################################################
ASSETS_URL="https://raw.githubusercontent.com/hasan7n/mockcube/451e95e3bd62a7112ffd3336302d4cddd895d0cb"

# datasets
DSET_A_URL="$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
DSET_B_URL="${ASSETS_URL}/assets/datasets/dataset_b.tar.gz"
DSET_C_URL="${ASSETS_URL}/assets/datasets/dataset_c.tar.gz"
DEMO_URL="${ASSETS_URL}/assets/datasets/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$ASSETS_URL/prep/mlcube/mlcube.yaml"
PREP_PARAMS="$ASSETS_URL/prep/mlcube/workspace/parameters.yaml"

# model cubes
FAILING_MODEL_MLCUBE="$ASSETS_URL/model-bug/mlcube/mlcube.yaml" # doesn't fail with association
MODEL_MLCUBE="$ASSETS_URL/model-cpu/mlcube/mlcube.yaml"
MODEL_ADD="$ASSETS_URL/assets/weights/weights1.tar.gz"
MODEL1_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters1.yaml"
MODEL2_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters2.yaml"
MODEL3_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters3.yaml"
MODEL4_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters4.yaml"

# metrics cubes
METRIC_MLCUBE="$ASSETS_URL/metrics/mlcube/mlcube.yaml"
METRIC_PARAMS="$ASSETS_URL/metrics/mlcube/workspace/parameters.yaml"

# admin token
ADMIN_TOKEN=$(curl -sk -X POST https://127.0.0.1:8000/auth-token/ -d '{"username": "admin", "password": "admin"}' -H 'Content-Type: application/json' | jq -r '.token')

# create users
MODELOWNER="mockmodelowner"
DATAOWNER="mockdataowner"
BENCHMARKOWNER="mockbenchmarkowner"
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "model", "last_name": "owner", "username": "'"$MODELOWNER"'", "password": "test", "email": "model@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "bmk", "last_name": "owner", "username": "'"$BENCHMARKOWNER"'", "password": "test", "email": "bmk@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "data", "last_name": "owner", "username": "'"$DATAOWNER"'", "password": "test", "email": "data@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"

##########################################################
################### Start Testing ########################
##########################################################


##########################################################
echo "=========================================="
echo "Setting and activating the testing profile"
echo "=========================================="
medperf profile create -n mocktest --server=${SERVER_URL} --certificate=${CERT_FILE}
checkFailed "Profile creation failed"
medperf profile activate mocktest
checkFailed "Profile activation failed"
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
echo "====================================="
echo "Login with modelowner"
echo "====================================="
medperf login --username=$MODELOWNER --password=test
checkFailed "modelowner login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

medperf mlcube submit --name prep -m $PREP_MLCUBE -p $PREP_PARAMS
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model2 -m $MODEL_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD
checkFailed "Model2 submission failed"
MODEL2_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model3 -m $MODEL_MLCUBE -p $MODEL3_PARAMS -a $MODEL_ADD
checkFailed "Model3 submission failed"
MODEL3_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model-fail -m $FAILING_MODEL_MLCUBE -p $MODEL4_PARAMS -a $MODEL_ADD
checkFailed "failing model submission failed"
FAILING_MODEL_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS
checkFailed "Metrics submission failed"
METRICS_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Login with benchmarkowner"
echo "====================================="
medperf login --username=$BENCHMARKOWNER --password=test
checkFailed "benchmarkowner login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit benchmark"
echo "====================================="
medperf benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-mlcube $PREP_UID --reference-model-mlcube $MODEL1_UID --evaluator-mlcube $METRICS_UID
checkFailed "Benchmark submission failed"
BMK_UID=$(medperf benchmark ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

curl -sk -X PUT https://127.0.0.1:8000/benchmarks/$BMK_UID/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
checkFailed "Benchmark approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Login with dataowner"
echo "====================================="
medperf login --username=$DATAOWNER --password=test
checkFailed "dataowner login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf dataset create -p $PREP_UID -d $DIRECTORY/dataset_a -l $DIRECTORY/dataset_a --name="dataset_a" --description="mock dataset a" --location="mock location a"
checkFailed "Data preparation step failed"
DSET_A_GENUID=$(medperf dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 1)
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data submission step"
echo "====================================="
medperf dataset submit -d $DSET_A_GENUID -y
checkFailed "Data submission step failed"
DSET_A_UID=$(medperf dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
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
echo "Login with benchmarkowner"
echo "====================================="
medperf login --username=$BENCHMARKOWNER --password=test
checkFailed "benchmarkowner login failed"
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
echo "Running model3 association"
echo "====================================="
medperf mlcube associate -m $MODEL3_UID -b $BMK_UID -y
checkFailed "Model3 association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running failing model association"
echo "====================================="
medperf mlcube associate -m $FAILING_MODEL_UID -b $BMK_UID -y
checkFailed "Failing model association failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Login with modelowner"
echo "====================================="
medperf login --username=$MODELOWNER --password=test
checkFailed "modelowner login failed"
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
echo "Login with dataowner"
echo "====================================="
medperf login --username=$DATAOWNER --password=test
checkFailed "dataowner login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running model2"
echo "====================================="
medperf run -b $BMK_UID -d $DSET_A_UID -m $MODEL2_UID -y
checkFailed "Model2 run failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running outstanding models"
echo "====================================="
medperf benchmark run -b $BMK_UID -d $DSET_A_UID
checkFailed "Model2 run failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Run failing cube with ignore errors"
echo "====================================="
medperf run -b $BMK_UID -d $DSET_A_UID -m $FAILING_MODEL_UID -y --ignore-errors
checkFailed "Failing mlcube run failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Delete mocktest profile"
echo "====================================="
medperf profile activate default
checkFailed "default profile activation failed"
medperf profile delete mocktest
checkFailed "Profile deletion failed"
##########################################################

if ${CLEANUP}; then
  clean
fi
