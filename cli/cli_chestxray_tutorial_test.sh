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
CERT_FILE="${AUTH_CERT:-$(dirname $(dirname $(realpath "$0")))/server/cert.crt}"
MEDPERF_STORAGE=~/.medperf
MEDPERF_SUBSTORAGE="$MEDPERF_STORAGE/$(echo $SERVER_URL | cut -d '/' -f 3 | sed -e 's/[.:]/_/g')"
MEDPERF_LOG_STORAGE="$MEDPERF_SUBSTORAGE/logs/medperf.log"
LOGIN_SCRIPT="$(dirname "$0")/auto_login.sh"

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
  medperf profile delete testbenchmark
  medperf profile delete testdata
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

# test users credentials
DATAOWNER="testdataowner@medperf.org"
BENCHMARKOWNER="testbenchmarkowner@medperf.org"

DATAOWNERPASSWORD="Dataset123"
BENCHMARKOWNERPASSWORD="Benchmark123"

if ${FRESH}; then
  clean
fi
echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
echo "downloading files to $DIRECTORY"
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_raw_data.tar.gz
tar -xzvf $DIRECTORY/sample_raw_data.tar.gz -C $DIRECTORY
chmod a+w $DIRECTORY/sample_raw_data

echo "=========================================="
echo "Creating test profiles for each user"
echo "=========================================="
medperf profile activate developement
checkFailed "developement profile creation failed"

medperf profile create -n testbenchmark
checkFailed "testbenchmark profile creation failed"
medperf profile create -n testdata
checkFailed "testdata profile creation failed"

echo "=========================================="
echo "Login each user"
echo "=========================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

timeout -k 30s 30s bash $LOGIN_SCRIPT -e $BENCHMARKOWNER -p $BENCHMARKOWNERPASSWORD
checkFailed "testbenchmark login failed"

medperf profile activate testdata
checkFailed "testdata profile activation failed"

timeout -k 30s 30s bash $LOGIN_SCRIPT -e $DATAOWNER -p $DATAOWNERPASSWORD
checkFailed "testdata login failed"

echo "====================================="
echo "Activate dataowner profile"
echo "====================================="
medperf profile activate testdata
checkFailed "testdata profile activation failed"
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf dataset create -b 1 -d $DIRECTORY/sample_raw_data/images -l $DIRECTORY/sample_raw_data/labels --name="nih_chestxray" --description="sample dataset" --location="mock location"
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
echo ""Activate benchmarkowner profile""
echo "====================================="
# Log in as the benchmark owner
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"
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
medperf profile activate testdata
checkFailed "testdata profile activation failed"
# Create results
medperf run -b 1 -d $DSET_UID -m 4 -y
checkFailed "Benchmark execution step failed"

echo "====================================="
echo "Logout users"
echo "====================================="
medperf profile activate testbenchmark
checkFailed "testbenchmark profile activation failed"

medperf auth logout
checkFailed "logout failed"

medperf profile activate testdata
checkFailed "testdata profile activation failed"

medperf auth logout
checkFailed "logout failed"


echo "====================================="
echo "Delete test profiles"
echo "====================================="
medperf profile activate default
checkFailed "default profile activation failed"

medperf profile delete testbenchmark
checkFailed "Profile deletion failed"

medperf profile delete testdata
checkFailed "Profile deletion failed"

if ${CLEANUP}; then
  clean
fi