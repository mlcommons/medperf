while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

# copy over changes from be_Dockerfile to Dockerfile
cp ./project/be_Dockerfile ./project/Dockerfile

if ${BUILD_BASE}; then
    git clone https://github.com/hasan7n/openfl.git
    cd openfl
    git checkout be_enable_partial_epochs
    docker build \
	    --build-arg http_proxy="http://proxy-us.intel.com:912"   \
	    --build-arg https_proxy="http://proxy-us.intel.com:912"  \
	    -t local/openfl:local -f openfl-docker/Dockerfile.base .
    cd ..
    rm -rf openfl
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always -Pdocker.build_args="--build-arg http_proxy='http://proxy-us.intel.com:912' --build-arg https_proxy='http://proxy-us.intel.com:912'"
