while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

if ${BUILD_BASE}; then
    git clone https://github.com/hasan7n/openfl.git
    cd openfl
    git checkout d0f6df8ea91e0eaaeabf0691caf0286162df5bd7
    docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
    cd ..
    rm -rf openfl
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
