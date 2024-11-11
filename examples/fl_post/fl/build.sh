while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

if ${BUILD_BASE}; then
    git clone https://github.com/hasan7n/openfl.git
    cd openfl
    git checkout 9467f829687b6284a6e380d31f90d31bc9de023f
    docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
    cd ..
    rm -rf openfl
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
