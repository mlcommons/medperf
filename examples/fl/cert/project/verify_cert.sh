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

if [ -z "$MEDPERF_INPUT_CN" ]; then
    echo "MEDPERF_INPUT_CN environment variable must be set"
    exit 1
fi

export STEPPATH=$pki_assets/.step

CERT_PATH=$pki_assets/crt.crt

mkdir -p /tmp/root_ca
/bin/sh /mlcube_project/trust.sh --ca_config $ca_config --pki_assets /tmp/root_ca

ROOT_CERT=/tmp/root_ca/root_ca.crt

step certificate verify $CERT_PATH --roots $ROOT_CERT

EXITSTATUS="$?"
if [ $EXITSTATUS -ne "0" ]; then
    echo "Failed to get the root certificate"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi


CN=$(step certificate inspect --short --format json "$CERT_PATH" | jq -r '.subject.cn')

if [ "$CN" = "$MEDPERF_INPUT_CN" ]; then
    echo "✅ Certificate CN matches expected value."
else
    echo "❌ CN mismatch! Found: $CN, Expected: $MEDPERF_INPUT_CN"
    exit 1
fi

# cleanup
rm -rf $STEPPATH
