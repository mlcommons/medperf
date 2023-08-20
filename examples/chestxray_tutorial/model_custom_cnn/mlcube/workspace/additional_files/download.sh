url=https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz
filename=$(basename $url)

if [ -x "$(which wget)" ] ; then
    wget $url
elif [ -x "$(which curl)" ]; then
    curl -o $filename $url
fi

tar -xf $filename
rm $filename
