#!/bin/bash

# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Copy the data preparation container
cp -r ../examples/chestxray_tutorial/data_preparator data_preparator

# Copy the FL training container config
mkdir -p fl_container
cp ../examples/flower/fl/container_config.yaml fl_container/container_config.yaml

# Copy the training plan config
cp ../examples/flower/fl/workspace/training_config.yaml training_config.yaml

# Download sample training datasets (two collaborator datasets)
url=https://storage.googleapis.com/medperf-storage/chestxray_train_sample1.tar.gz
filename=$(basename $url)

if [ -x "$(which wget)" ]; then
    wget $url
elif [ -x "$(which curl)" ]; then
    curl -o $filename $url
fi

tar -xf $filename
rm $filename

mkdir -p sample_raw_data
mv chestxray_train_sample1/dataset_1 sample_raw_data/col1
mv chestxray_train_sample1/dataset_2 sample_raw_data/col2
rm -rf chestxray_train_sample1

echo "testdo@example.com: testdo@example.com" >>./cols_list.yaml
echo "testdo2@example.com: testdo2@example.com" >>./cols_list.yaml