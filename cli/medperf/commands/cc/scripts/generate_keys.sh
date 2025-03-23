#!/bin/bash

while getopts k:c: flag; do
    case "${flag}" in
    k) KEY_PATH=${OPTARG} ;;
    c) CERT_PATH=${OPTARG} ;;
    esac
done

if [[ -z "$KEY_PATH" || -z "$CERT_PATH" ]]; then
    echo "Usage: $0 -k <priv key path> -c <pub key path>" >&2
    exit 1
fi

openssl genpkey -algorithm ed25519 >$KEY_PATH
openssl pkey -in $KEY_PATH -pubout -out $CERT_PATH
