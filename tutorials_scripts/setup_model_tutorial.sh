# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Copy the MLCube to be used
cp -r ../examples/chestxray_tutorial/model_mobilenetv2 model_mobilenetv2

## download model weights
cd model_mobilenetv2/mlcube/workspace/additional_files
sh download.sh
rm download.sh

## Login locally as model owner
cd ..
sh tutorials_scripts/medperf_login.sh testdo@example.com