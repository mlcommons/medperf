#! /bin/bash
cd server
sh setup-dev-server.sh -r 1
SERVER_PID=$(jobs | grep "sh setup-dev-server.sh" | tr -s ' ' | cut -d ' ' -f 1 | tr -dc '0-9')
cd ..
sleep 15
bash cli/cli_tests.sh -f
EXIT_CODE=$?
if [ "$EXIT_CODE" -ne "0" ]; then
  echo "CLI test failed"
fi
kill %$SERVER_PID
echo "Test finished with status $EXIT_CODE"
exit $EXIT_CODE
