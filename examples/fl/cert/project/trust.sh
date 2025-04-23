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

rm -rf $pki_assets/root_ca.crt

if [ -n "$CA_FINGERPRINT" ]; then
    # trust the CA.
    step ca root $pki_assets/root_ca.crt --ca-url $CA_ADDRESS:$CA_PORT \
        --fingerprint $CA_FINGERPRINT
else
    curl -o $pki_assets/root_ca.crt $CA_ADDRESS:$CA_PORT/roots.pem
fi
EXITSTATUS="$?"
if [ $EXITSTATUS -ne "0" ]; then
    echo "Failed to retrieve the root certificate"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

# cleanup
rm -rf $STEPPATH
