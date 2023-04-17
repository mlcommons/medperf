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
  medperf profile delete localtest
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
echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
echo "downloading files to $DIRECTORY"
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/mock_chexpert.tar.gz
tar -xzvf $DIRECTORY/mock_chexpert.tar.gz -C $DIRECTORY
chmod a+w $DIRECTORY/mock_chexpert
echo "====================================="
echo "Setting testing profile"
echo "====================================="
medperf profile create -n localtest --server=${SERVER_URL} --certificate=${CERT_FILE}
medperf profile activate localtest
echo "====================================="
echo "Logging the user with username: testdataowner and password: test"
echo "====================================="
medperf login --username=testdataowner --password=test
checkFailed "Login failed"
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf dataset create -b 1 -d $DIRECTORY/mock_chexpert/images -l $DIRECTORY/mock_chexpert/labels --name="mock_chexpert" --description="mock dataset" --location="mock location"
checkFailed "Data preparation step failed"

echo "\n"
DSET_UID=$(medperf dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 1)
echo "Dataset UID: $DSET_UID"
echo "====================================="
echo "Registering dataset with medperf"
echo "====================================="
medperf dataset submit -d $DSET_UID -y
checkFailed "Data registration step failed"

DSET_UID=$(medperf dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "Dataset UID: $DSET_UID"
echo "====================================="
echo "Creating dataset benchmark association"
echo "====================================="
medperf dataset associate -d $DSET_UID -b 1 -y
checkFailed "Data association step failed"

echo "====================================="
echo "Approving dataset association"
echo "====================================="
# Log in as the benchmark owner
medperf login --username=testbenchmarkowner --password=test
# Get association information
ASSOC_INFO=$(medperf association ls | head -n 4 | tail -n 1 | tr -s ' ')
ASSOC_DSET_UID=$(echo $ASSOC_INFO | cut -d ' ' -f 1)
ASSOC_BMK_UID=$(echo $ASSOC_INFO | cut -d ' ' -f 2)
# Mark dataset-benchmark association as approved
medperf association approve -b $ASSOC_BMK_UID -d $ASSOC_DSET_UID
checkFailed "Association approval failed"

echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
# log back as user
medperf login --username=testdataowner --password=test
# Create results
medperf run -b 1 -d $DSET_UID -m 2 -y
checkFailed "Benchmark execution step failed"

echo "====================================="
echo "Delete localtest profile"
echo "====================================="
medperf profile activate default
checkFailed "default profile activation failed"
medperf profile delete localtest
checkFailed "Profile deletion failed"

if ${CLEANUP}; then
  clean
fi