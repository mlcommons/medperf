cp -r ./mlcube ./mlcube_agg
cp -r ./mlcube ./mlcube_col1
cp -r ./mlcube ./mlcube_col2

mkdir ./mlcube_agg/workspace/node_cert ./mlcube_agg/workspace/ca_cert
mkdir ./mlcube_col1/workspace/node_cert ./mlcube_col1/workspace/ca_cert
mkdir ./mlcube_col2/workspace/node_cert ./mlcube_col2/workspace/ca_cert
mkdir ./ca

HOSTNAME_=$(hostname -A | cut -d " " -f 1)

# root ca
openssl genpkey -algorithm RSA -out ca/root.key -pkeyopt rsa_keygen_bits:3072
openssl req -x509 -new -nodes -key ca/root.key -sha384 -days 36500 -out ca/root.crt \
    -subj "/DC=org/DC=simple/CN=Simple Root CA/O=Simple Inc/OU=Simple Root CA"

# col1
sed -i '/^commonName = /c\commonName = col1' csr.conf
sed -i '/^DNS\.1 = /c\DNS.1 = col1' csr.conf
cd mlcube_col1/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd ../../../

# col2
sed -i '/^commonName = /c\commonName = col2' csr.conf
sed -i '/^DNS\.1 = /c\DNS.1 = col2' csr.conf
cd mlcube_col2/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd ../../../

# agg
sed -i "/^commonName = /c\commonName = $HOSTNAME_" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $HOSTNAME_" csr.conf
cd mlcube_agg/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_server
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd ../../../

# network file
echo "agg_addr: $HOSTNAME_" >>mlcube_col1/workspace/network.yaml
echo "agg_port: 50273" >>mlcube_col1/workspace/network.yaml
echo "address: $HOSTNAME_" >>mlcube_col1/workspace/network.yaml
echo "port: 50273" >>mlcube_col1/workspace/network.yaml

cp mlcube_col1/workspace/network.yaml mlcube_col2/workspace/network.yaml
cp mlcube_col1/workspace/network.yaml mlcube_agg/workspace/network.yaml

# cols file
echo "col1" >>mlcube_agg/workspace/cols.yaml
echo "col2" >>mlcube_agg/workspace/cols.yaml

# data download
cd mlcube_col1/workspace/
wget https://storage.googleapis.com/medperf-storage/testfl/col1_prepared.tar.gz
tar -xf col1_prepared.tar.gz
rm col1_prepared.tar.gz
cd ../..

cd mlcube_col2/workspace/
wget https://storage.googleapis.com/medperf-storage/testfl/col2_prepared.tar.gz
tar -xf col2_prepared.tar.gz
rm col2_prepared.tar.gz
cd ../..

# weights download
cd mlcube_agg/workspace/
mkdir additional_files
cd additional_files
wget https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz
tar -xf init_weights_miccai.tar.gz
rm init_weights_miccai.tar.gz
cd ../../..
