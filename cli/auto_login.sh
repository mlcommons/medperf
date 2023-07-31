#! /bin/bash

unset -v EMAIL

while getopts e: flag
do
    case "${flag}" in
        e) EMAIL=${OPTARG};;
    esac
done

: ${EMAIL:?Missing -e}


get_url() {
  while read -r line <&"$1"; do
    if [ $(echo $line | grep "^https://") ]; then
        echo $line
        break
    fi
  done
}

coproc medperf auth login -e $EMAIL
sleep 2

PROC_STREAM=${COPROC[0]}
URL=$(get_url $PROC_STREAM)

LOGIN_SCRIPT="$(dirname "$0")/auto_login.py"
python $LOGIN_SCRIPT --email $EMAIL --url $URL

wait ${COPROC_PID}
