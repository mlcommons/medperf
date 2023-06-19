#! /bin/bash

unset -v EMAIL
unset -v PASSWORD

while getopts e:p: flag
do
    case "${flag}" in
        e) EMAIL=${OPTARG};;
        p) PASSWORD=${OPTARG};;
    esac
done

: ${EMAIL:?Missing -e}
: ${PASSWORD:?Missing -p}


get_url() {
  while read -r line $1; do
    if [ $(echo $line | grep "^https://") ]; then
        echo $line
        break
    fi
  done
}

coproc medperf auth login
sleep 2
URL=$(get_url <&"${COPROC[0]}")
python "$(dirname "$0")/auto_login.py" --email $EMAIL --password $PASSWORD --url $URL
wait ${COPROC_PID}
