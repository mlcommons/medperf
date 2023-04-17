# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download a clean, unpackaged demo dataset
wget https://storage.googleapis.com/medperf-storage/mock_xrv_demo_data.tar.gz
tar -xf xrv_demo_data.tar.gz
rm xrv_demo_data.tar.gz
rm paths.yaml

# Copy the MLCubes to be used
cp -r ../examples/ChestXRay/chexpert_prep chexpert_prep
cp -r ../examples/ChestXRay/xrv_chex_densenet xrv_chex_densenet
cp -r ../examples/ChestXRay/metrics metrics
