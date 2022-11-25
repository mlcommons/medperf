#! /bin/bash
while getopts u:p:s:d:c:a: flag
do
    case "${flag}" in
        u) USERNAME_=${OPTARG};;
        p) PASS=${OPTARG};;
        s) SERVER_URL=${OPTARG};;
        d) DIRECTORY=${OPTARG};;
        c) CLEANUP="true";;
        a) AUTH_CERT=${OPTARG};;
    esac
done
USERNAME_="${USERNAME_:-admin}"
PASS="${PASS:-admin}"
SERVER_URL="${SERVER_URL:-https://127.0.0.1:8000}"
DIRECTORY="${DIRECTORY:-/tmp}"
CLEANUP="${CLEANUP:-false}"
CERT_FILE="${AUTH_CERT:-$(realpath ~/.medperf.crt)}"
MEDPERF_STORAGE=~/.medperf_test
MEDPERF_LOG_STORAGE="${MEDPERF_STORAGE}/logs/medperf.log"

echo "username: $USERNAME_"
echo "password: $PASS"
echo "Server URL: $SERVER_URL"
echo "Storage location: $MEDPERF_STORAGE"
echo "Certificate: $CERT_FILE"

if ${CLEANUP}; then
  echo "====================================="
  echo "Cleaning up medperf tmp files"
  echo "====================================="
  rm $DIRECTORY/mock_chexpert.tar.gz
  rm -fr $DIRECTORY/mock_chexpert
  rm -fr $MEDPERF_STORAGE
fi
echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
echo "downloading files to $DIRECTORY"
wget -P $DIRECTORY https://storage.googleapis.com/medperf-storage/mock_chexpert_dset.tar.gz
tar -xzvf $DIRECTORY/mock_chexpert_dset.tar.gz -C $DIRECTORY
chmod a+w $DIRECTORY/mock_chexpert
ls $DIRECTORY/mock_chexpert
ls $DIRECTORY/mock_chexpert/valid
echo "====================================="
echo "Logging the user with username: ${USERNAME_} and password: ${PASS}"
echo "====================================="
medperf --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=${USERNAME_} --password=${PASS}
if [ "$?" -ne "0" ]; then
  echo "Login failed"
  tail "$MEDPERF_LOG_STORAGE"
  exit 1
fi
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
medperf --certificate $CERT_FILE --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE dataset create -b 1 -d $DIRECTORY/mock_chexpert -l $DIRECTORY/mock_chexpert --name="mock_chexpert" --description="mock dataset" --location="mock location"
if [ "$?" -ne "0" ]; then
  echo "Data preparation step failed"
  tail "$MEDPERF_LOG_STORAGE"
  exit 2
fi
echo "\n"
DSET_UID=$(medperf --certificate $CERT_FILE --storage=$MEDPERF_STORAGE --host=$SERVER_URL dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 1)
echo "Dataset UID: $DSET_UID"
echo "====================================="
echo "Registering dataset with medperf"
echo "====================================="
medperf --certificate $CERT_FILE --storage=$MEDPERF_STORAGE --host=$SERVER_URL dataset submit -d $DSET_UID -y
if [ "$?" -ne "0" ]; then
  echo "Data registration step failed"
  cat "$MEDPERF_STORAGE/medperf.log"
  exit 2
fi
echo "====================================="
echo "Creating dataset benchmark association"
echo "====================================="
medperf --certificate $CERT_FILE --storage=$MEDPERF_STORAGE --host=$SERVER_URL dataset associate -d $DSET_UID -b 1 -y
if [ "$?" -ne "0" ]; then
  echo "Data registration step failed"
  cat "$MEDPERF_STORAGE/medperf.log"
  exit 2
fi
echo "====================================="
echo "Approving dataset association"
echo "====================================="
# Log in as the benchmark owner
medperf --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=testbenchmarkowner --password=test
# Get association information
ASSOC_INFO=$(medperf --certificate $CERT_FILE --storage=$MEDPERF_STORAGE --host=$SERVER_URL association ls | head -n 4 | tail -n 1 | tr -s ' ')
ASSOC_DSET_UID=$(echo $ASSOC_INFO | cut -d ' ' -f 1)
ASSOC_BMK_UID=$(echo $ASSOC_INFO | cut -d ' ' -f 2)
# Mark dataset-benchmark association as approved
medperf --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE association approve -b $ASSOC_BMK_UID -d $ASSOC_DSET_UID
if [ "$?" -ne "0" ]; then
  echo "Association approval failed"
  cat "$MEDPERF_STORAGE/medperf.log"
  exit 2
fi
echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
# log back as user
medperf --certificate $CERT_FILE --host=${SERVER_URL} --storage=$MEDPERF_STORAGE login --username=${USERNAME_} --password=${PASS}
# Create results
medperf --certificate $CERT_FILE --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE run -b 1 -d $DSET_UID -m 2 -y
if [ "$?" -ne "0" ]; then
  echo "Benchmark execution step failed"
  tail $MEDPERF_LOG_STORAGE
  exit 3
fi
if ${CLEANUP}; then
  echo "====================================="
  echo "Cleaning up medperf tmp files"
  echo "====================================="
  rm $DIRECTORY/mock_chexpert.tar.gz
  rm -fr $DIRECTORY/mock_chexpert
  rm -fr $MEDPERF_STORAGE
fi