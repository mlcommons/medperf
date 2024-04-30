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

medperf mlcube run --mlcube ../mock_cert/mlcube --task trust
mv ../mock_cert/mlcube/workspace/pki_assets/* ./ca

# col1
medperf mlcube run --mlcube ../mock_cert/mlcube --task get_client_cert -e MEDPERF_INPUT_CN=$COL1_CN
mv ../mock_cert/mlcube/workspace/pki_assets/* ./mlcube_col1/workspace/node_cert
cp -r ./ca/* ./mlcube_col1/workspace/ca_cert

# col2
medperf mlcube run --mlcube ../mock_cert/mlcube --task get_client_cert -e MEDPERF_INPUT_CN=$COL2_CN
mv ../mock_cert/mlcube/workspace/pki_assets/* ./mlcube_col2/workspace/node_cert
cp -r ./ca/* ./mlcube_col2/workspace/ca_cert

# col3
if ${TWO_COL_SAME_CERT}; then
    cp mlcube_col2/workspace/node_cert/* mlcube_col3/workspace/node_cert
    cp mlcube_col2/workspace/ca_cert/* mlcube_col3/workspace/ca_cert
else
    medperf mlcube run --mlcube ../mock_cert/mlcube --task get_client_cert -e MEDPERF_INPUT_CN=$COL3_CN
    mv ../mock_cert/mlcube/workspace/pki_assets/* ./mlcube_col3/workspace/node_cert
    cp -r ./ca/* ./mlcube_col3/workspace/ca_cert
fi

medperf mlcube run --mlcube ../mock_cert/mlcube --task get_server_cert -e MEDPERF_INPUT_CN=$HOSTNAME_
mv ../mock_cert/mlcube/workspace/pki_assets/* ./mlcube_agg/workspace/node_cert
cp -r ./ca/* ./mlcube_agg/workspace/ca_cert

# aggregator_config
echo "address: $HOSTNAME_" >>mlcube_agg/workspace/aggregator_config.yaml
echo "port: 50273" >>mlcube_agg/workspace/aggregator_config.yaml

# cols file
echo "$COL1_LABEL: $COL1_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL2_LABEL: $COL2_CN" >>mlcube_agg/workspace/cols.yaml
echo "$COL3_LABEL: $COL3_CN" >>mlcube_agg/workspace/cols.yaml

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

cp -r mlcube_col2/workspace/data mlcube_col3/workspace
cp -r mlcube_col2/workspace/labels mlcube_col3/workspace

# weights download
cd mlcube_agg/workspace/
mkdir additional_files
cd additional_files
wget https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz
tar -xf init_weights_miccai.tar.gz
rm init_weights_miccai.tar.gz
cd ../../..
