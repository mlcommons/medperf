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

if [ -z "$MEDPERF_INPUT_CN" ]; then
    echo "MEDPERF_INPUT_CN environment variable must be set"
    exit 1
fi

CA_ADDRESS=$(jq -r '.address' $ca_config)
CA_PORT=$(jq -r '.port' $ca_config)
CA_FINGERPRINT=$(jq -r '.fingerprint' $ca_config)
CA_CLIENT_PROVISIONER=$(jq -r '.client_provisioner' $ca_config)
CA_SERVER_PROVISIONER=$(jq -r '.server_provisioner' $ca_config)

export STEPPATH=$pki_assets/.step

if [ "$task" = "get_server_cert" ]; then
    PROVISIONER_ARGS="--provisioner $CA_SERVER_PROVISIONER"
elif [ "$task" = "get_client_cert" ]; then
    PROVISIONER_ARGS="--provisioner $CA_CLIENT_PROVISIONER --console"
else
    echo "Invalid task: Task should be get_server_cert or get_client_cert"
    exit 1
fi

if [ -z "$CA_FINGERPRINT" ]; then
    echo "Empty fingerprint."
    exit 1
fi

cert_path=$pki_assets/crt.crt
key_path=$pki_assets/key.key

if [ -e $STEPPATH ]; then
    echo ".step folder already exists"
    exit 1
fi

if [ -e $cert_path ]; then
    echo "cert file already exists"
    exit 1
fi

if [ -e $key_path ]; then
    echo "key file already exists"
    exit 1
fi

# First, try to bootstrap the root cert using step-ca. This will also verify the fingerprint.
step ca bootstrap --ca-url $CA_ADDRESS:$CA_PORT \
        --fingerprint $CA_FINGERPRINT
if [ "$?" -eq "0" ]; then
    ROOT=$STEPPATH/certs/root_ca.crt
else
    # if the above fails, it could be that the CA is reachable via https using system trusted certs.
    mkdir -p /tmp/root_ca
    /bin/sh /mlcube_project/trust.sh --ca_config $ca_config --pki_assets /tmp/root_ca
    if [ "$?" -ne "0" ]; then
        echo "Failed to verify the root certificate"
        # cleanup
        rm -rf $STEPPATH
        exit 1
    fi
    ROOT=/etc/ssl/certs/ca-certificates.crt
fi

# generate private key and ask for a certificate
step ca certificate --ca-url $CA_ADDRESS:$CA_PORT \
    --root $ROOT \
    --kty=RSA \
    $PROVISIONER_ARGS \
    $MEDPERF_INPUT_CN $cert_path $key_path

EXITSTATUS="$?"
if [ $EXITSTATUS -ne "0" ]; then
    echo "Failed to get the certificate"
    # cleanup
    rm -rf $STEPPATH
    exit 1
fi

# cleanup
rm -rf $STEPPATH
