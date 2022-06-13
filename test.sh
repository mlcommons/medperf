#! /bin/bash
rm -fr ~/.medperf_test
rm -f db.sqlite3
python server/manage.py migrate
python server/manage.py runserver >& /dev/null &
SERVER_PID=$(jobs | grep "python server/manage.py runserver" | tr -s ' ' | cut -d ' ' -f 1 | tr -dc '0-9')
sleep 2
pip install -r server/test-requirements.txt
python server/seed.py
bash cli/cli.sh -l
EXIT_CODE=$?
if [ "$EXIT_CODE" -ne "0" ]; then
  echo "CLI test failed"
fi
kill %$SERVER_PID
echo "Test finished with status $EXIT_CODE"
exit $EXIT_CODE
