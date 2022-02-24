#! /bin/bash
while getopts u:p:s:d:c:l flag
do
    case "${flag}" in
        u) USERNAME=${OPTARG};;
        p) PASS=${OPTARG};;
        s) SERVER_URL=${OPTARG};;
        d) DIRECTORY=${OPTARG};;
        c) CLEANUP="true";;
        l) LOCAL="true" ;;
    esac
done
USERNAME="${USERNAME:-testdataowner}"
PASS="${PASS:-test}"
SERVER_URL="${SERVER_URL:-http://127.0.0.1:8000}"
DIRECTORY="${DIRECTORY:-/tmp}"
CLEANUP="${CLEANUP:-false}"
MEDPERF_STORAGE="~/.medperf_test"
LOCAL="${LOCAL:-""}"

echo "username: $USERNAME"
echo "password: $PASS"
echo "Server URL: $SERVER_URL"
echo "Storage location: $MEDPERF_STORAGE"
echo "Running local config: $LOCAL"

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
echo "Logging the user with username: ${USERNAME} and password: ${PASS}"
echo "====================================="
echo ${LOCAL:+'-e'} "${USERNAME}\n${PASS}\n" | medperf --ui STDIN --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE login 
if [ "$?" -ne "0" ]; then
  echo "Login failed"
  cat "$MEDPERF_STORAGE/medperf.log"
  exit 1
fi
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
echo ${LOCAL:+'-e'} "Y\nname\ndescription\nlocation\nY\nY\n" | medperf --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE dataset create -b 1 -d $DIRECTORY/mock_chexpert -l $DIRECTORY/mock_chexpert
if [ "$?" -ne "0" ]; then
  echo "Data preparation step failed"
  cat "$MEDPERF_STORAGE/medperf.log"
  exit 2
fi
echo "\n"
DSET_UID=$(medperf --storage=$MEDPERF_STORAGE --host=$SERVER_URL dataset ls | tail -n 1 | tr -s ' ' | cut -d ' ' -f 1)
echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
echo ${LOCAL:+'-e'} "Y\n" | medperf --host=$SERVER_URL --log=DEBUG --storage=$MEDPERF_STORAGE execute -b 1 -d $DSET_UID -m 2
if [ "$?" -ne "0" ]; then
  echo "Benchmark execution step failed"
  cat $MEDPERF_STORAGE/medperf.log
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