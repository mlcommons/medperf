#! /bin/bash
rm -fr ~/.medperf
rm -f server/db.sqlite3
python server/manage.py migrate
python server/manage.py runserver >& /dev/null &
SERVER_PID=$(jobs | grep "python server/manage.py runserver" | tr -s ' ' | cut -d ' ' -f 1 | tr -dc '0-9')
sleep 2
sh server/server.sh
bash cli/cli.sh
if [ "$?" -ne "0" ]; then
  echo "CLI test failed"
  exit "$?"
fi
kill %$SERVER_PID
echo "Success"
