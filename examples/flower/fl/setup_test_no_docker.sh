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

cp -r ./workspace ./workspace_agg
cp -r ./workspace ./workspace_col1
cp -r ./workspace ./workspace_col2
cp -r ./workspace ./workspace_col3

mkdir ./workspace_agg/node_cert ./workspace_agg/ca_cert
mkdir ./workspace_col1/node_cert ./workspace_col1/ca_cert
mkdir ./workspace_col2/node_cert ./workspace_col2/ca_cert
mkdir ./workspace_col3/node_cert ./workspace_col3/ca_cert
mkdir ./ca

HOSTNAME_=$(hostname -I | cut -d " " -f 1)
PORT_=50273
ADMIN_PORT_=50274
rm .env
touch .env
echo "HOSTNAME_=$HOSTNAME_" >> .env
echo "PORT_=$PORT_" >> .env
echo "ADMIN_PORT_=$ADMIN_PORT_" >> .env

# root ca
openssl genpkey -algorithm RSA -out ca/root.key -pkeyopt rsa_keygen_bits:3072
openssl req -x509 -new -nodes -key ca/root.key -sha384 -days 36500 -out ca/root.crt \
    -subj "/DC=org/DC=simple/CN=Simple Root CA/O=Simple Inc/OU=Simple Root CA"

# col1
sed -i "/^commonName = /c\commonName = $COL1_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL1_CN" csr.conf
cd workspace_col1/node_cert
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -out key.key
openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../csr.conf
rm csr.csr
cp ../../ca/root.crt ../ca_cert/
cd ../../

# col2
sed -i "/^commonName = /c\commonName = $COL2_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL2_CN" csr.conf
cd workspace_col2/node_cert
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -out key.key
openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../csr.conf
rm csr.csr
cp ../../ca/root.crt ../ca_cert/
cd ../../

# col3
if ${TWO_COL_SAME_CERT}; then
    cp workspace_col2/node_cert/* workspace_col3/node_cert
    cp workspace_col2/ca_cert/* workspace_col3/ca_cert
else
    sed -i "/^commonName = /c\commonName = $COL3_CN" csr.conf
    sed -i "/^DNS\.1 = /c\DNS.1 = $COL3_CN" csr.conf
    cd workspace_col3/node_cert
    openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -out key.key
    openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_client
    openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
        -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../csr.conf
    rm csr.csr
    cp ../../ca/root.crt ../ca_cert/
    cd ../../
fi

# agg
sed -i "/^commonName = /c\commonName = $HOSTNAME_" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $HOSTNAME_" csr.conf
cd workspace_agg/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_server
openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_server_crt -extfile ../../csr.conf
rm csr.csr
cp ../../ca/root.crt ../ca_cert/
cd ../../

# aggregator_config
echo "address: $HOSTNAME_" >>workspace_agg/aggregator_config.yaml
echo "port: $PORT_" >>workspace_agg/aggregator_config.yaml
echo "admin_port: $ADMIN_PORT_" >>workspace_agg/aggregator_config.yaml

# cols file
COL1_PUBKEY_B64=$(openssl x509 -in workspace_col1/node_cert/crt.crt -noout -pubkey | base64 -w 0)
COL2_PUBKEY_B64=$(openssl x509 -in workspace_col2/node_cert/crt.crt -noout -pubkey | base64 -w 0)
COL3_PUBKEY_B64=$(openssl x509 -in workspace_col3/node_cert/crt.crt -noout -pubkey | base64 -w 0)
echo "$COL1_CN: $COL1_PUBKEY_B64" >>workspace_agg/cols.yaml
echo "$COL2_CN: $COL2_PUBKEY_B64" >>workspace_agg/cols.yaml
echo "$COL3_CN: $COL3_PUBKEY_B64" >>workspace_agg/cols.yaml

# data download
cd workspace_col1/
wget https://storage.googleapis.com/medperf-storage/col1_chestxray_prepared.tar.gz
tar -xf col1_chestxray_prepared.tar.gz
rm col1_chestxray_prepared.tar.gz
cd ..

cp -r workspace_col1/data workspace_col2/data
cp -r workspace_col1/labels workspace_col2/labels

cp -r workspace_col2/data workspace_col3/data
cp -r workspace_col2/labels workspace_col3/labels

# weights download
cd workspace_agg/
mkdir additional_files
cd additional_files
wget https://storage.googleapis.com/medperf-storage/init_weights_flower.tar.gz
tar -xf init_weights_flower.tar.gz
rm init_weights_flower.tar.gz
cd ../..

# for admin
ADMIN_CN="testfladmin@example.com"

mkdir ./for_admin
mkdir ./for_admin/node_cert

sed -i "/^commonName = /c\commonName = $ADMIN_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $ADMIN_CN" csr.conf
cd for_admin/node_cert
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -out key.key
openssl req -new -key key.key -out csr.csr -config ../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../ca/root.crt -CAkey ../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../csr.conf
rm csr.csr
mkdir ../ca_cert
cp -r ../../ca/root.crt ../ca_cert/root.crt
cd ../..
