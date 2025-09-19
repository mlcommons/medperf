# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download the training data splits

url1=https://storage.googleapis.com/medperf-storage/nvflare_training/uncol1.tar.gz
url2=https://storage.googleapis.com/medperf-storage/nvflare_training/uncol2.tar.gz

filename1=$(basename $url1)
filename2=$(basename $url2)

if [ -x "$(which wget)" ]; then
    wget $url1
    wget $url2
elif [ -x "$(which curl)" ]; then
    curl -o $filename1 $url1
    curl -o $filename2 $url2
fi

tar -xf $filename1
tar -xf $filename2
rm $filename1
rm $filename2
mv uncol1 col1
mv uncol2 col2

echo "participants: [testdo@example.com, testdo2@example.com]" >>./cols_list.yaml
cp ../tutorial_scripts/collab_shortcut.sh collab_shortcut.sh

# Copy the training config to be used
cp -r ../examples/nvfl/fl/node/workspace/training_config training_config

# Copy the container implementations
cp -r ../examples/chestxray_tutorial/data_preparator/ data_preparator
cp -r ../examples/nvfl/fl/node/ node_container
rm -rf node_container/workspace
cp -r ../examples/nvfl/fl/admin/ admin_container
