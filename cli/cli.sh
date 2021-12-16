#! /bin/bash
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
echo -e "testdataowner\ntest\n" | medperf --ui STDIN login
if [ "$?" -ne "0" ]; then
  echo "Login failed"
  exit 1
fi
echo "\n"
echo "====================================="
echo "Running data preparation step"
echo "====================================="
echo -e "Y\nname\ndescription\nlocation\nY\n" | medperf prepare -b 1 -d /tmp/mock_chexpert -l /tmp/mock_chexpert/valid.csv
if [ "$?" -ne "0" ]; then
  echo "Data preparation step failed"
  exit 2
fi
echo "\n"
DSET_UID=$(medperf datasets | tail -n 1 | tr -s ' ' | cut -d ' ' -f 2)
echo "====================================="
echo "Running benchmark execution step"
echo "====================================="
echo -e "Y\n" | medperf execute -b 1 -d $DSET_UID -m 2
if [ "$?" -ne "0" ]; then
  echo "Benchmark execution step failed"
  exit 3
fi
echo "====================================="
echo "Cleaning up medperf tmp files"
echo "====================================="
rm /tmp/mock_chexpert.tar.gz
rm -fr /tmp/mock_chexpert