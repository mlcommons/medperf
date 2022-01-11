#! /bin/bash
while getopts u:p:s:d: flag
do
    case "${flag}" in
        u) USERNAME=${OPTARG};;
        p) PASS=${OPTARG};;
        s) SERVER_URL=${OPTARG};;
        d) DIRECTORY=${OPTARG};;
    esac
done
USERNAME="${USERNAME:-testdataowner}"
PASS="${PASS:-test}"
SERVER_URL="${SERVER_URL:-http://127.0.0.1:8000}"
DIRECTORY="${DIRECTORY:-/tmp}"

echo "username: $USERNAME"
echo "password: $PASS"
echo "Server URL: $SERVER_URL"

echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
wget -P "${DIRECTORY}" https://storage.googleapis.com/medperf-storage/mock_chexpert_dset.tar.gz
tar -xzvf "${DIRECTORY}/mock_chexpert_dset.tar.gz" -C $DIRECTORY
chmod a+w "${DIRECTORY}/mock_chexpert"
echo "====================================="
echo "Logging the user with username: ${USERNAME} and password: ${PASS}"
echo "====================================="
echo "${USERNAME}\n${PASS}\n" | medperf --ui STDIN --host=$SERVER_URL login
if [ "$?" -ne "0" ]; then
  echo "Login failed"
  cat ~/.medperf/medperf.log
  exit 1
fi
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
echo "Y\nname\ndescription\nlocation\nY\n" | medperf --host=$SERVER_URL prepare -b 1 -d $DIRECTORY/mock_chexpert -l $DIRECTORY/mock_chexpert/valid.csv
if [ "$?" -ne "0" ]; then
  echo "Data preparation step failed"
  cat ~/.medperf/medperf.log
  exit 2
fi
echo "\n"
DSET_UID=$(medperf datasets | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
echo "Y\n" | medperf --host=$SERVER_URL execute -b 1 -d $DSET_UID -m 2
if [ "$?" -ne "0" ]; then
  echo "Benchmark execution step failed"
  cat ~/.medperf/medperf.log
  exit 3
fi
echo "====================================="
echo "Cleaning up medperf tmp files"
echo "====================================="
rm $DIRECTORY/mock_chexpert.tar.gz
rm -fr $DIRECTORY/mock_chexpert
rm -fr ~/.medperf