mlcube run --mlcube ./mlcube/mlcube.yaml --task trust
# sh clean.sh
mlcube run --mlcube ./mlcube/mlcube.yaml --task get_client_cert -Pdocker.env_args="-e MEDPERF_INPUT_CN=user@example.com"
sh clean.sh
mlcube run --mlcube ./mlcube/mlcube.yaml --task get_server_cert -Pdocker.env_args="-e MEDPERF_INPUT_CN=https://example.com"
sh clean.sh
