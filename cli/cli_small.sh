#! /bin/bash
while getopts s:d:c:a: flag
do
    case "${flag}" in
        s) SERVER_URL=${OPTARG};;
        d) DIRECTORY=${OPTARG};;
        c) CLEANUP="true";;
        a) AUTH_CERT=${OPTARG};;
    esac
done

SERVER_URL="${SERVER_URL:-https://127.0.0.1:8000}"
DIRECTORY="${DIRECTORY:-/tmp/medperf_test_files}"
CLEANUP="${CLEANUP:-false}"
CERT_FILE="${AUTH_CERT:-$(realpath ~/.medperf.crt)}"
MEDPERF_STORAGE=~/.medperf_test
MEDPERF_LOG_STORAGE="${MEDPERF_STORAGE}/logs/medperf.log"
MEDCLEAN=--no-cleanup

echo "Server URL: $SERVER_URL"
echo "Storage location: $MEDPERF_STORAGE"
echo "Certificate: $CERT_FILE"

# frequently used
clean(){
  if ${CLEANUP}; then
    echo "====================================="
    echo "Cleaning up medperf tmp files"
    echo "====================================="
    rm -fr $DIRECTORY
    rm -fr $MEDPERF_STORAGE
  fi
}
checkFailed(){
  if [ "$?" -ne "0" ]; then
    echo $1
    tail "$MEDPERF_LOG_STORAGE"
    clean
    exit 1
  fi
}


clean
##########################################################
########################## Setup #########################
##########################################################
ASSETS_URL="https://raw.githubusercontent.com/hasan7n/mockcube/ebecacaf22689ec9ea0d20826c805a206e2c63e0"

# datasets
DSET_A_URL="$ASSETS_URL/assets/datasets/dataset_a.tar.gz"
DSET_B_URL="${ASSETS_URL}/assets/datasets/dataset_b.tar.gz"
DSET_C_URL="${ASSETS_URL}/assets/datasets/dataset_c.tar.gz"
DEMO_URL="${ASSETS_URL}/assets/datasets/demo_dset1.tar.gz"

# prep cubes
PREP_MLCUBE="$ASSETS_URL/prep/mlcube/mlcube.yaml"
PREP_PARAMS="$ASSETS_URL/prep/mlcube/workspace/parameters.yaml"

# model cubes
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

# UIDs
BMK_UID=1

PREP_UID=1
MODEL1_UID=2
METRICS_UID=3
MODEL2_UID=4
MODEL3_UID=5
MODEL4_UID=6

# create users
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "model", "last_name": "owner", "username": "testmodelowner", "password": "test", "email": "model@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "bmk", "last_name": "owner", "username": "testbenchmarkowner", "password": "test", "email": "bmk@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
curl -sk -X POST https://127.0.0.1:8000/users/ -d '{"first_name": "data", "last_name": "owner", "username": "testdataowner", "password": "test", "email": "data@owner.com"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"

##########################################################
################### Start Testing ########################
##########################################################


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
echo "Login with testmodelowner"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=testmodelowner --password=test
checkFailed "Login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit cubes"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name prep -m $PREP_MLCUBE -p $PREP_PARAMS
checkFailed "Prep submission failed"

medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name model1 -m $MODEL_MLCUBE -p $MODEL1_PARAMS -a $MODEL_ADD
checkFailed "Model1 submission failed"

medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name metrics -m $METRIC_MLCUBE -p $METRIC_PARAMS
checkFailed "Metrics submission failed"

medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name model2 -m $MODEL_MLCUBE -p $MODEL2_PARAMS -a $MODEL_ADD
checkFailed "Model2 submission failed"

medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name model3 -m $MODEL_MLCUBE -p $MODEL3_PARAMS -a $MODEL_ADD
checkFailed "Model3 submission failed"

medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE mlcube submit --name model4 -m $MODEL_MLCUBE -p $MODEL4_PARAMS -a $MODEL_ADD
checkFailed "Model4 submission failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Login with testbenchmarkowner"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=testbenchmarkowner --password=test
checkFailed "Login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Submit benchmark"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE benchmark submit --name bmk --description bmk --demo-url $DEMO_URL --data-preparation-mlcube $PREP_UID --reference-model-mlcube $MODEL1_UID --evaluator-mlcube $METRICS_UID
checkFailed "Benchmark submission failed"
curl -sk -X PUT https://127.0.0.1:8000/benchmarks/$BMK_UID/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Token $ADMIN_TOKEN"
checkFailed "Benchmatk approval failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Login with testdataowner"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=testdataowner --password=test
checkFailed "Login failed"
##########################################################

echo "\n"

##########################################################
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf $MEDCLEAN --certificate $CERT_FILE --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE dataset create -p $PREP_UID -d $DIRECTORY/dataset_a -l $DIRECTORY/dataset_a --name="dataset_a" --description="mock dataset a" --location="mock location a"
checkFailed "Data preparation step failed"
##########################################################

echo "\n"

clean
