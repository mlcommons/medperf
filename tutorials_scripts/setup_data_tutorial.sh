# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download a dataset
url=https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_raw_data.tar.gz
filename=$(basename $url)

if [ -x "$(which wget)" ] ; then
    wget $url
elif [ -x "$(which curl)" ]; then
    curl -o $filename $url
fi
tar -xf $filename
rm $filename

## Login locally as data owner
medperf auth login -e testdo@example.com