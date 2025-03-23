#! /bin/bash
while getopts s:t:i:k: flag; do
    case "${flag}" in
    s) SOURCE=${OPTARG} ;;
    t) TARGET=${OPTARG} ;;
    i) SECRET_ID=${OPTARG} ;;
    k) KBS_STORAGE=${OPTARG} ;;
    esac
done

if [[ -z "$SOURCE" || -z "$TARGET" || -z "$SECRET_ID" || -z "$KBS_STORAGE" ]]; then
    echo "Usage: $0 -s <source> -t <target> -i <secret_id> -k <kbs_storage>" >&2
    exit 1
fi

SECRET_PATH=$KBS_STORAGE/$SECRET_ID
mkdir -p $(dirname "$SECRET_PATH")

head -c 32 /dev/urandom | openssl enc >$SECRET_PATH

mkdir output
mkdir input

skopeo copy docker-daemon:$SOURCE dir:input

docker run -v "$PWD/output:/output" -v "$PWD/input:/input" ghcr.io/confidential-containers/staged-images/coco-keyprovider:latest /encrypt.sh \
    -k "$(base64 <$SECRET_PATH)" \
    -i kbs:///$SECRET_ID \
    -s dir:/input \
    -d dir:/output

skopeo copy dir:output docker://$TARGET

rm -rf output
rm -rf input
