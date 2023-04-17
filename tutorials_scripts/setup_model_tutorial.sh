# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Copy the MLCube to be used
cp -r ../examples/ChestXRay/xrv_densenet xrv_densenet

## use pc model instead of chex
rm xrv_densenet/mlcube/workspace/parameters.yaml
rm xrv_densenet/mlcube/workspace/additional_files/weights.pt
mv xrv_densenet/mlcube/workspace/parameters_pc.yaml xrv_densenet/mlcube/workspace/parameters.yaml
mv xrv_densenet/mlcube/workspace/additional_files/weights_pc.pt xrv_densenet/mlcube/workspace/additional_files/weights.pt
