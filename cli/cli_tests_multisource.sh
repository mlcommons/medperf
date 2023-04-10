#! /bin/bash

# This script is for manual testing only.
# It prompts the user with Synapse credentials
# And it expects certain assets to be already uploaded on Synapse


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

SERVER_URL="${SERVER_URL:-https://localhost:8000}"
DIRECTORY="${DIRECTORY:-/tmp/medperf_test_files}"
CLEANUP="${CLEANUP:-false}"
FRESH="${FRESH:-false}"
CERT_FILE="${AUTH_CERT:-$(realpath $(dirname $(dirname "$0")))/server/cert.crt}"
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
ASSETS_URL="https://raw.githubusercontent.com/hasan7n/mockcube/b9e862ea68a5f07a5ab5b0d45a68c7bc47d921fa"

# datasets
DEMO_URL="${ASSETS_URL}/assets/datasets/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$ASSETS_URL/prep/mlcube/mlcube.yaml"
PREP_PARAMS="$ASSETS_URL/prep/mlcube/workspace/parameters.yaml"

# model cubes
MODEL_MLCUBE="$ASSETS_URL/model-cpu/mlcube/mlcube.yaml"
MODEL_ADD="synapse:syn51089171"
MODEL1_PARAMS="$ASSETS_URL/model-cpu/mlcube/workspace/parameters1.yaml"
PREP_SING_IMAGE="direct:$ASSETS_URL/prep/mlcube/workspace/.image/mock-prep.simg"
MODEL_SING_IMAGE="synapse:syn51080138"

METRICS_SING_IMAGE="$ASSETS_URL/metrics/mlcube/workspace/.image/mock-metrics.simg"

# metrics cubes
METRIC_MLCUBE="$ASSETS_URL/metrics/mlcube/mlcube.yaml"
METRIC_PARAMS="$ASSETS_URL/metrics/mlcube/workspace/parameters.yaml"

# admin token
ADMIN_TOKEN=$(curl -sk -X POST $SERVER_URL/auth-token/ -d '{"username": "admin", "password": "admin"}' -H 'Content-Type: application/json' | jq -r '.token')

# create users
MODELOWNER="mockmodelowner"
DATAOWNER="mockdataowner"
BENCHMARKOWNER="mockbenchmarkowner"
curl -sk -X POST $SERVER_URL/users/ -d '{"first_name": "model", "last_name": "owner", "username": "'"$MODELOWNER"'", "password": "test", "email": "model@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST $SERVER_URL/users/ -d '{"first_name": "bmk", "last_name": "owner", "username": "'"$BENCHMARKOWNER"'", "password": "test", "email": "bmk@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST $SERVER_URL/users/ -d '{"first_name": "data", "last_name": "owner", "username": "'"$DATAOWNER"'", "password": "test", "email": "data@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"

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
echo "Synapse Login"
echo "====================================="
medperf synapse_login
checkFailed "Synapse Login login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="

medperf mlcube submit --name prep -m $PREP_MLCUBE -p $PREP_PARAMS -i $PREP_SING_IMAGE
checkFailed "Prep submission failed"
PREP_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD -i $MODEL_SING_IMAGE
checkFailed "Model1 submission failed"
MODEL1_UID=$(medperf mlcube ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)

medperf mlcube submit --name metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS -i $METRICS_SING_IMAGE
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
medperf --platform singularity benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-mlcube $PREP_UID --reference-model-mlcube $MODEL1_UID --evaluator-mlcube $METRICS_UID
checkFailed "Benchmark submission failed"
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
