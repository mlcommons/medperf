while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

if ${BUILD_BASE}; then
    git clone https://github.com/hasan7n/openfl.git
    cd openfl
    git checkout b5e26ac33935966800b6a5b61e85b823cc68c4da
    docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
    cd ..
    rm -rf openfl
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
