# Create a workspace
original_dir=$(echo $PWD)
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download a clean, unpackaged demo dataset
url=https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz
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
cp -r ../examples/chestxray_tutorial/data_preparator data_preparator
cp -r ../examples/chestxray_tutorial/metrics metrics
cp -r ../examples/chestxray_tutorial/model_custom_cnn model_custom_cnn

## download model weights
cd model_custom_cnn/mlcube/workspace/additional_files
sh download.sh
rm download.sh

## Login locally as benchmark owner
cd $original_dir
sh tutorials_scripts/medperf_login.sh testbo@example.com