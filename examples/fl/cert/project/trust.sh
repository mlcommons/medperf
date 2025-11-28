#!/bin/bash

# Read arguments
# --ca_config: config file of the CA containing address, port, and root cert fingerprint
# --pki_assets: output path to store the CA root cert

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

pki_assets=${pki_assets%/}

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

# First, try to download the root cert using step-ca. This will also verify the fingerprint.
step ca root $ROOT_CERT_PATH --ca-url $CA_ADDRESS:$CA_PORT \
    --fingerprint $CA_FINGERPRINT

if [ "$?" -eq "0" ]; then
    echo "Root cert retrieved successfully using step ca root."
    # cleanup
    rm -rf $STEPPATH
    exit 0
fi

# if the above fails, it could be that the CA is reachable via https using system trusted certs.
# Try to fetch the root cert using curl then verify the fingerprint.
# NOTE: code below isn't tested yet.

echo "Trying to retrieve the root cert using curl..."

curl -o $ROOT_CERT_PATH $CA_ADDRESS:$CA_PORT/roots.pem

if [ "$?" -ne "0" ]; then
    echo "Failed to retrieve the root certificate"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

echo "Verifying the fingerprint..."

FINGERPRINT_CALC=$(step certificate fingerprint "$ROOT_CERT_PATH")
if [ "$FINGERPRINT_CALC" != "$CA_FINGERPRINT" ]; then
    echo "Failed to retrieve the root certificate: fingerprint mismatch"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

# cleanup
rm -rf $STEPPATH
