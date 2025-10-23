#!/bin/bash

# Read arguments
while [ "${1:-}" != "" ]; do
    case "$1" in
    "--ca_config"*)
        ca_config="${1#*=}"
        ;;
    "--pki_assets"*)
        pki_assets="${1#*=}"
        ;;
    *)
        task=$1
        ;;
    esac
    shift
done

# validate arguments
if [ -z "$ca_config" ]; then
    echo "--ca_config is required"
    exit 1
fi

if [ -z "$pki_assets" ]; then
    echo "--pki_assets is required"
    exit 1
fi

if [ "$task" != "trust" ]; then
    echo "Invalid task: Task should be 'trust'"
    exit 1
fi

export STEPPATH=$pki_assets/.step

CA_ADDRESS=$(jq -r '.address' $ca_config)
CA_PORT=$(jq -r '.port' $ca_config)
CA_FINGERPRINT=$(jq -r '.fingerprint' $ca_config)
ROOT_CERT_PATH=$pki_assets/root_ca.crt

if [ -z "$CA_FINGERPRINT" ]; then
    echo "Empty fingerprint."
    exit 1
fi

rm -rf $ROOT_CERT_PATH

# First, try to download the root cert using step. This will also verify the fingerprint.
step ca root $ROOT_CERT_PATH --ca-url $CA_ADDRESS:$CA_PORT \
    --fingerprint $CA_FINGERPRINT

if [ "$?" -eq "0" ]; then
    # cleanup
    rm -rf $STEPPATH
    exit 0
fi

# if the above fails, it could be that the CA is behind a proxy.
# Try to fetch the root cert using curl then verify the fingerprint.

curl -o $ROOT_CERT_PATH $CA_ADDRESS:$CA_PORT/roots.pem

if [ "$?" -ne "0" ]; then
    echo "Failed to retrieve the root certificate"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

FINGERPRINT_CALC=$(step certificate fingerprint "$ROOT_CERT_PATH")
if [ "$FINGERPRINT_CALC" != "$CA_FINGERPRINT" ]; then
    echo "Failed to retrieve the root certificate: fingerprint mismatch"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

# cleanup
rm -rf $STEPPATH
