# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download a clean, unpackaged demo dataset
url=https://storage.googleapis.com/medperf-storage/mock_xrv_demo_data.tar.gz 
filename=$(basename $url)

if [ -x "$(which wget)" ] ; then
    wget $url
elif [ -x "$(which curl)" ]; then
    curl -o $filename $url
fi
tar -xf $filename
rm $filename
rm paths.yaml

# Copy the MLCubes to be used
cp -r ../examples/ChestXRay/chexpert_prep chexpert_prep
cp -r ../examples/ChestXRay/metrics metrics
cp -r ../examples/ChestXRay/xrv_densenet xrv_densenet

## remove redundant files
rm xrv_densenet/mlcube/workspace/parameters_pc.yaml
rm xrv_densenet/mlcube/workspace/additional_files/weights_pc.pt
