#!/bin/bash

while getopts a:k:c: flag; do
    case "${flag}" in
    a) ADDRESS=${OPTARG} ;;
    k) KEY_PATH=${OPTARG} ;;
    c) CERT_PATH=${OPTARG} ;;
    esac
done

if [[ -z "$ADDRESS" || -z "$KEY_PATH" || -z "$CERT_PATH" ]]; then
    echo "Usage: $0 -a <address> -k <key path> -c <cert path>" >&2
    exit 1
fi

# Generate the private key and self-signed cert directly
openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$KEY_PATH" \
    -out "$CERT_PATH" \
    -subj "/C=CN/ST=dummy/L=dummy/O=localhost/OU=Development/CN=$ADDRESS" \
    -addext "subjectAltName=IP:$ADDRESS"
