#! /bin/bash
rm -fr ~/.medperf_test
cd server
sh setup-dev-server.sh -c cert.crt -k cert.key -r 1 -p ~/.medperf_test.crt -r 1 &
SERVER_PID=$(jobs | grep "sh setup-dev-server.sh" | tr -s ' ' | cut -d ' ' -f 1 | tr -dc '0-9')
cd ..
sleep 15
pip install -r server/test-requirements.txt
python server/seed.py --cert ~/.medperf_test.crt
bash cli/cli.sh -l
EXIT_CODE=$?
if [ "$EXIT_CODE" -ne "0" ]; then
  echo "CLI test failed"
fi
kill %$SERVER_PID
echo "Test finished with status $EXIT_CODE"
exit $EXIT_CODE
