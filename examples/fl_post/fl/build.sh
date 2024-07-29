while getopts b flag; do
    case "${flag}" in
    b) BUILD_BASE="true" ;;
    esac
done
BUILD_BASE="${BUILD_BASE:-false}"

if ${BUILD_BASE}; then
    # git clone https://github.com/hasan7n/openfl.git
    # cd openfl
    # git checkout 8c75ddb252930dd6306885a55d0bb9bd0462c333
    # docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
    # # cd ..
    # rm -rf openfl
    
    cd /home/msheller/git/openfl-hasan
    cd -
fi
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
