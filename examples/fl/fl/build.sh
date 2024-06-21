git clone https://github.com/securefederatedai/openfl.git
cd openfl
git checkout e6f3f5fd4462307b2c9431184190167aa43d962f
docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
cd ..
rm -rf openfl
mlcube configure --mlcube ./mlcube -Pdocker.build_strategy=always
