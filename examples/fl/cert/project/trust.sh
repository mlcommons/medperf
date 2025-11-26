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
        ;;
    esac
    shift
done

# validate arguments
if [ -z "$ca_config" ]; then
    ca_config="/mlcommons/volumes/ca_config/ca_config.json"
fi

if [ -z "$pki_assets" ]; then
    pki_assets="/mlcommons/volumes/pki_assets"
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

# First, try to download the root cert using step-ca. This will also verify the fingerprint.
step ca root $ROOT_CERT_PATH --ca-url $CA_ADDRESS:$CA_PORT \
    --fingerprint $CA_FINGERPRINT

if [ "$?" -eq "0" ]; then
    # cleanup
    rm -rf $STEPPATH
    exit 0
fi

# if the above fails, it could be that the CA is reachable via https using system trusted certs.
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
