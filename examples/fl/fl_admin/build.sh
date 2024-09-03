while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

if ${BUILD_BASE}; then
    git clone https://github.com/hasan7n/openfl.git
    cd openfl
    git checkout 7c9d4e7039f51014a4f7b3bedf5e2c7f1d353e68
    docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
    cd ..
    rm -rf openfl
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
