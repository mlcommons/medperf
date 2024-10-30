while getopts t flag; do
    case "${flag}" in
    t) TWO_COL_SAME_CERT="true" ;;
    esac
done
TWO_COL_SAME_CERT="${TWO_COL_SAME_CERT:-false}"

COL1_CN="col1@example.com"
COL2_CN="col2@example.com"
COL3_CN="col3@example.com"
COL1_LABEL="col1@example.com"
COL2_LABEL="col2@example.com"
COL3_LABEL="col3@example.com"

if ${TWO_COL_SAME_CERT}; then
    COL1_CN="org1@example.com"
    COL2_CN="org2@example.com"
    COL3_CN="org2@example.com" # in this case this var is not used actually. it's OK
fi

cp -r ./mlcube ./mlcube_agg
cp -r ./mlcube ./mlcube_col1
cp -r ./mlcube ./mlcube_col2
cp -r ./mlcube ./mlcube_col3

mkdir ./mlcube_agg/workspace/node_cert ./mlcube_agg/workspace/ca_cert
mkdir ./mlcube_col1/workspace/node_cert ./mlcube_col1/workspace/ca_cert
mkdir ./mlcube_col2/workspace/node_cert ./mlcube_col2/workspace/ca_cert
mkdir ./mlcube_col3/workspace/node_cert ./mlcube_col3/workspace/ca_cert
mkdir ./ca

HOSTNAME_=$(hostname -A | cut -d " " -f 1)

# root ca
openssl genpkey -algorithm RSA -out ca/root.key -pkeyopt rsa_keygen_bits:3072
openssl req -x509 -new -nodes -key ca/root.key -sha384 -days 36500 -out ca/root.crt \
    -subj "/DC=org/DC=simple/CN=Simple Root CA/O=Simple Inc/OU=Simple Root CA"

# col1
sed -i "/^commonName = /c\commonName = $COL1_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL1_CN" csr.conf
cd mlcube_col1/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd ../../../

# col2
sed -i "/^commonName = /c\commonName = $COL2_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL2_CN" csr.conf
cd mlcube_col2/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd ../../../

# col3
if ${TWO_COL_SAME_CERT}; then
    cp mlcube_col2/workspace/node_cert/* mlcube_col3/workspace/node_cert
    cp mlcube_col2/workspace/ca_cert/* mlcube_col3/workspace/ca_cert
else
    sed -i "/^commonName = /c\commonName = $COL3_CN" csr.conf
    sed -i "/^DNS\.1 = /c\DNS.1 = $COL3_CN" csr.conf
    cd mlcube_col3/workspace/node_cert
    openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
    openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
    openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
        -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
    rm csr.csr
    cp ../../../ca/root.crt ../ca_cert/
    cd ../../../
fi

# agg
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

# cols file
echo "$COL1_LABEL: $COL1_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL2_LABEL: $COL2_CN" >>mlcube_agg/workspace/cols.yaml

# for admin
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

# data setup
cd mlcube_col1/workspace
wget https://storage.googleapis.com/medperf-storage/fltest29July/small_test_data1.tar.gz
tar -xf small_test_data1.tar.gz
mv small_test_data1/* .
rm -rf small_test_data1.tar.gz
rm -rf small_test_data1
cd ../../

cd mlcube_col2/workspace
wget https://storage.googleapis.com/medperf-storage/fltest29July/small_test_data2.tar.gz
tar -xf small_test_data2.tar.gz
mv small_test_data2/* .
rm -rf small_test_data2.tar.gz
rm -rf small_test_data2
cd ../../

cd mlcube_col3/workspace
wget https://storage.googleapis.com/medperf-storage/fltest29July/small_test_data3.tar.gz
tar -xf small_test_data3.tar.gz
mv small_test_data3/* .
rm -rf small_test_data3.tar.gz
rm -rf small_test_data3
cd ../../

# weights setup
cd mlcube/workspace
mkdir additional_files
cd additional_files
wget https://storage.googleapis.com/medperf-storage/fltest29July/flpost_add29july.tar.gz
tar -xf flpost_add29july.tar.gz
rm flpost_add29july.tar.gz
cd ../../../
cp -r mlcube/workspace/additional_files mlcube_agg/workspace/additional_files
cp -r mlcube/workspace/additional_files mlcube_col1/workspace/additional_files
cp -r mlcube/workspace/additional_files mlcube_col2/workspace/additional_files
cp -r mlcube/workspace/additional_files mlcube_col3/workspace/additional_files
