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

DECRYPTED_ARCHIVE="data.tar.gz"
openssl enc -d -aes-256-cbc -salt -pbkdf2 -in "$ENCRYPTED_FILE" -out "$DECRYPTED_ARCHIVE" -pass file:"$SECRET_PATH"
mkdir -p $DATA_FOLDER
tar -xzf "$DECRYPTED_ARCHIVE" -C $DATA_FOLDER
rm "$DECRYPTED_ARCHIVE"
