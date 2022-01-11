#! /bin/bash
while getopts u:p:s: flag
do
    case "${flag}" in
        u) ADMIN_USERNAME=${OPTARG};;
        p) ADMIN_PASS=${OPTARG};;
        s) SERVER_URL=${OPTARG};;
    esac
done
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
SERVER_URL="${SERVER_URL:-http://127.0.0.1:8000}"

echo "Admin username: $ADMIN_USERNAME"
echo "Admin password: $ADMIN_PASS"
echo "Server URL: $SERVER_URL"

echo "====================================="
echo "Cleaning up medperf tmp files"
echo "====================================="
rm /tmp/mock_chexpert.tar.gz
rm -fr /tmp/mock_chexpert
rm -fr ~/.medperf
echo "====================================="
echo "Retrieving mock dataset"
echo "====================================="
wget -P /tmp https://storage.googleapis.com/medperf-storage/mock_chexpert_dset.tar.gz &> /dev/null
tar -xzvf /tmp/mock_chexpert_dset.tar.gz -C /tmp &> /dev/null
echo "====================================="
echo "Logging the user to medperf"
echo "====================================="
echo -e "${ADMIN_USERNAME}\n${ADMIN_PASS}\n" | medperf --ui STDIN --host=$SERVER_URL login
if [ "$?" -ne "0" ]; then
  echo "Login failed"
  exit 1
fi
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
echo -e "Y\nname\ndescription\nlocation\nY\n" | medperf --host=$SERVER_URL prepare -b 1 -d /tmp/mock_chexpert -l /tmp/mock_chexpert/valid.csv
if [ "$?" -ne "0" ]; then
  echo "Data preparation step failed"
  exit 2
fi
echo "\n"
DSET_UID=$(medperf datasets | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
echo -e "Y\n" | medperf --host=$SERVER_URL execute -b 1 -d $DSET_UID -m 2
if [ "$?" -ne "0" ]; then
  echo "Benchmark execution step failed"
  exit 3
fi
echo "====================================="
echo "Cleaning up medperf tmp files"
echo "====================================="
rm /tmp/mock_chexpert.tar.gz
rm -fr /tmp/mock_chexpert