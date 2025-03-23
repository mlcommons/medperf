#!/bin/bash

while getopts d:e:s: flag; do
    case "${flag}" in
    d) DATA_FOLDER=${OPTARG} ;;
    e) ENCRYPTED_FILE=${OPTARG} ;;
    s) SECRET_PATH=${OPTARG} ;;
    esac
done

if [[ -z "$DATA_FOLDER" || -z "$ENCRYPTED_FILE" || -z "$SECRET_PATH" ]]; then
    echo "Usage: $0 -d <data_folder> -e <encrypted_file> -s <secret_path>" >&2
    exit 1
fi

head -c 32 /dev/urandom | openssl enc >"$SECRET_PATH"
ARCHIVE="data.tar.gz"
tar -czf "$ARCHIVE" -C $DATA_FOLDER data labels
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$ARCHIVE" -out "$ENCRYPTED_FILE" -pass file:"$SECRET_PATH"
rm "$ARCHIVE"
