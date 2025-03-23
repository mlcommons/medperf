#!/bin/bash

while getopts n:k:c: flag; do
    case "${flag}" in
    n) NAME=${OPTARG} ;;
    k) KEY_PATH=${OPTARG} ;;
    c) CERT_PATH=${OPTARG} ;;
    esac
done

if [[ -z "$NAME" || -z "$KEY_PATH" || -z "$CERT_PATH" ]]; then
    echo "Usage: $0 -n <name> -k <key path> -c <cert path>" >&2
    exit 1
fi

openssl ecparam -name $NAME -genkey -noout -out $KEY_PATH
openssl req -new -x509 -key $KEY_PATH -out $CERT_PATH -days 365
