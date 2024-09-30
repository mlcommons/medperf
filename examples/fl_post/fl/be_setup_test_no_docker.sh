while getopts t flag; do
    case "${flag}" in
    t) TWO_COL_SAME_CERT="true" ;;
    esac
done
TWO_COL_SAME_CERT="${TWO_COL_SAME_CERT:-false}"

COL1_CN="col1@example.com"
COL2_CN="col2@example.com"
COL3_CN="col3@example.com"
COL4_CN="col4@example.com"
COL5_CN="col5@example.com"

COL1_LABEL="col1@example.com"
COL2_LABEL="col2@example.com"
COL3_LABEL="col3@example.com"
COL4_LABEL="col4@example.com"
COL5_LABEL="col5@example.com"

if ${TWO_COL_SAME_CERT}; then
    COL1_CN="org1@example.com"
    COL2_CN="org2@example.com"
    COL3_CN="org3@example.com"
    COL4_CN="org4@example.com"
    COL5_CN="org5@example.com" # in this case this var is not used actually.
fi

HOMEDIR="/raid/edwardsb/projects/RANO/hasan_medperf/examples/fl_post/fl"

cd $HOMEDIR

mkdir mlcube_agg
mkdir mlcube_col1
mkdir mlcube_col2
mkdir mlcube_col3
mkdir mlcube_col4
mkdir mlcube_col5



cp -r ./mlcube/* ./mlcube_agg
cp -r ./mlcube/* ./mlcube_col1
cp -r ./mlcube/* ./mlcube_col2
cp -r ./mlcube/* ./mlcube_col3
cp -r ./mlcube/* ./mlcube_col4
cp -r ./mlcube/* ./mlcube_col5

mkdir ./mlcube_agg/workspace/node_cert ./mlcube_agg/workspace/ca_cert
mkdir ./mlcube_col1/workspace/node_cert ./mlcube_col1/workspace/ca_cert
mkdir ./mlcube_col2/workspace/node_cert ./mlcube_col2/workspace/ca_cert
mkdir ./mlcube_col3/workspace/node_cert ./mlcube_col3/workspace/ca_cert
mkdir ./mlcube_col4/workspace/node_cert ./mlcube_col4/workspace/ca_cert
mkdir ./mlcube_col5/workspace/node_cert ./mlcube_col5/workspace/ca_cert
mkdir ca

HOSTNAME_=$(hostname -A | cut -d " " -f 1)
# HOSTNAME_=$(hostname -I | cut -d " " -f 1)


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
cd $HOMEDIR

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
cd $HOMEDIR

# col3
if ${TWO_COL_SAME_CERT}; then
    never goes here cp mlcube_col2/workspace/node_cert/* mlcube_col3/workspace/node_cert
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
    cd $HOMEDIR
fi

# col4
sed -i "/^commonName = /c\commonName = $COL4_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL4_CN" csr.conf
cd mlcube_col4/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd $HOMEDIR

# col5
sed -i "/^commonName = /c\commonName = $COL5_CN" csr.conf
sed -i "/^DNS\.1 = /c\DNS.1 = $COL5_CN" csr.conf
cd mlcube_col5/workspace/node_cert
openssl genpkey -algorithm RSA -out key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key key.key -out csr.csr -config ../../../csr.conf -extensions v3_client
openssl x509 -req -in csr.csr -CA ../../../ca/root.crt -CAkey ../../../ca/root.key \
    -CAcreateserial -out crt.crt -days 36500 -sha384 -extensions v3_client_crt -extfile ../../../csr.conf
rm csr.csr
cp ../../../ca/root.crt ../ca_cert/
cd $HOMEDIR



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
cd $HOMEDIR

# aggregator_config
echo "address: $HOSTNAME_" >> mlcube_agg/workspace/aggregator_config.yaml
echo "port: 50273" >>mlcube_agg/workspace/aggregator_config.yaml

# cols file
echo "$COL1_LABEL: $COL1_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL2_LABEL: $COL2_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL3_LABEL: $COL3_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL4_LABEL: $COL4_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL5_LABEL: $COL5_CN" >>mlcube_agg/workspace/cols.yaml

# for admin
ADMIN_CN="admin@example.com"

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
cd $HOMEDIR

# THIS IS BRANDON'S CODE COPYING IN THE SAME DATA
mkdir mlcube_col1/workspace/labels
mkdir mlcube_col1/workspace/data

mkdir mlcube_col2/workspace/labels
mkdir mlcube_col2/workspace/data

mkdir mlcube_col3/workspace/labels
mkdir mlcube_col3/workspace/data

mkdir mlcube_col4/workspace/labels
mkdir mlcube_col4/workspace/data

mkdir mlcube_col5/workspace/labels
mkdir mlcube_col5/workspace/data

# DATA_DIR="test_data_links_testforhasan"
# DATA_DIR="test_data_links_random_times_0"
# DATA_DIR="test_data_links"

# this is the one I had success running on
#DATA_DIRS=test_data_small_from_hasan

SIZE="hundred"
#SIZE="thousand"

DATA_DIR_1="test_${SIZE}_BraTS20_3square_0"
DATA_DIR_2="test_${SIZE}_BraTS20_3square_1"
DATA_DIR_3="test_${SIZE}_BraTS20_3square_2"
DATA_DIR_4="test_${SIZE}_BraTS20_3square_3"
DATA_DIR_5="test_${SIZE}_BraTS20_3square_4"

cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_1/labels/* mlcube_col1/workspace/labels
cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_1/data/* mlcube_col1/workspace/data

cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_2/labels/* mlcube_col2/workspace/labels
cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_2/data/* mlcube_col2/workspace/data

cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_3/labels/* mlcube_col3/workspace/labels
cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_3/data/* mlcube_col3/workspace/data

cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_4/labels/* mlcube_col4/workspace/labels
cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_4/data/* mlcube_col4/workspace/data

cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_5/labels/* mlcube_col5/workspace/labels
cp -r /raid/edwardsb/projects/RANO/$DATA_DIR_5/data/* mlcube_col5/workspace/data

# wget https://storage.googleapis.com/medperf-storage/fltest29July/flpost_add29july.tar.gz I copied on spr01 into /home/edwardsb/repo_extras/hasan_medperperf_extras

# aggregator additional files
mkdir mlcube_agg/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_weights mlcube_agg/workspace/additional_files
# maybe I don't need the one immediately below (only for collaborators)
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_agg/workspace/additional_files

# col1 additional files
mkdir mlcube_col1/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_col1/workspace/additional_files

# col2 additional files
mkdir mlcube_col2/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_col2/workspace/additional_files

# col3 additional files
mkdir mlcube_col3/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_col3/workspace/additional_files

# col4 additional files
mkdir mlcube_col4/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_col4/workspace/additional_files

# col5 additional files
mkdir mlcube_col5/workspace/additional_files
cp -r /home/edwardsb/repo_extras/hasan_medperf_extras/download_from_hasan/init_nnunet mlcube_col5/workspace/additional_files


# source /home/edwardsb/virtual/hasan_medperf/bin/activate
