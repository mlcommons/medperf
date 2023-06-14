# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download a dataset
url=https://storage.googleapis.com/medperf-storage/mock_chexpert.tar.gz
filename=$(basename $url)

if [ -x "$(which wget)" ] ; then
    wget $url
elif [ -x "$(which curl)" ]; then
    curl -o $filename $url
fi
tar -xf $filename
