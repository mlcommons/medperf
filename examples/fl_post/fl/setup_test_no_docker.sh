while getopts n: flag; do
    case "${flag}" in
    n) NUM_COLS=${OPTARG} ;;
    esac
done
NUM_COLS="${NUM_COLS:-3}"

setupCA() {
    mkdir ./ca
    openssl genpkey -algorithm RSA -out ca/root.key -pkeyopt rsa_keygen_bits:3072
    openssl req -x509 -new -nodes -key ca/root.key -sha384 -days 36500 -out ca/root.crt \
        -subj "/DC=org/DC=simple/CN=Simple Root CA/O=Simple Inc/OU=Simple Root CA"

}

setupData() {
    wget https://storage.googleapis.com/medperf-storage/fltest29July/small_test_data.tar.gz
    tar -xf small_test_data.tar.gz
    rm -rf small_test_data.tar.gz
}

setupWeights() {
    # weights setup
    cd mlcube/workspace
    mkdir additional_files
    cd additional_files
    wget https://storage.googleapis.com/medperf-storage/flpost_add15dec.tar.gz
    tar -xf flpost_add15dec.tar.gz
    rm flpost_add15dec.tar.gz
    cd ../../../
}

setupAgg() {
    HOSTNAME_=$(hostname -A | cut -d " " -f 1)
    cp -r ./mlcube ./mlcube_agg
    mkdir ./mlcube_agg/workspace/node_cert ./mlcube_agg/workspace/ca_cert

    # cert
    sed -i "/^commonName = /c\commonName = $HOSTNAME_" csr.conf
    sed -i "/^DNS\.1 = /c\DNS.1 = $HOSTNAME_" csr.conf
    cd mlcube_agg/workspace/node_cert
    openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
    openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_server
    openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
        -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_server_crt -extfile ../../../csr.conf
    rm csr.csr
    cp ../../../ca/root.crt ../ca_cert/
    cd ../../../

    # aggregator_config
    echo "address: $HOSTNAME_" >>mlcube_agg/workspace/aggregator_config.yaml
    echo "port: 50273" >>mlcube_agg/workspace/aggregator_config.yaml

    # weights
    cp -r mlcube/workspace/additional_files mlcube_agg/workspace/additional_files

}

setupAdmin() {
    ADMIN_CN="testfladmin@example.com"

    mkdir ./for_admin
    mkdir ./for_admin/node_cert

    sed -i "/^commonName = /c\commonName = $ADMIN_CN" csr.conf
    sed -i "/^DNS\.1 = /c\DNS.1 = $ADMIN_CN" csr.conf
    cd for_admin/node_cert
    openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
    openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_client
    openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
        -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../csr.conf
    rm csr.csr
    mkdir ../ca_cert
    cp -r ../../ca/root.crt ../ca_cert/root.crt
    cd ../..
}

setupCol() {
    # $1 is ID
    N=$1
    COL_CN="col$N@example.com"
    COL_LABEL="col$N@example.com"
    cp -r ./mlcube ./mlcube_col$N
    mkdir ./mlcube_col$N/workspace/node_cert ./mlcube_col$N/workspace/ca_cert

    # cert
    sed -i "/^commonName = /c\commonName = $COL_CN" csr.conf
    sed -i "/^DNS\.1 = /c\DNS.1 = $COL_CN" csr.conf
    cd mlcube_col$N/workspace/node_cert
    openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
    openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
    openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
        -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
    rm csr.csr
    cp ../../../ca/root.crt ../ca_cert/
    cd ../../../

    # add in cols file
    echo "$COL_LABEL: $COL_CN" >>mlcube_agg/workspace/cols.yaml

    # weights
    cp -r mlcube/workspace/additional_files mlcube_col$N/workspace/additional_files

    # data
    mv small_test_data$N/* mlcube_col$N/workspace
}

setupCA
setupData
setupWeights
setupAgg
setupAdmin

a=0
while [ $a -lt $NUM_COLS ]; do
    a=$(expr $a + 1)
    setupCol $a
done
rm -r small_test_data*
