medperf mlcube run --mlcube ./mlcube --task trust
sh clean.sh
medperf mlcube run --mlcube ./mlcube --task get_client_cert -e MEDPERF_INPUT_CN=user@example.com
sh clean.sh
medperf mlcube run --mlcube ./mlcube --task get_server_cert -e MEDPERF_INPUT_CN=https://example.com
sh clean.sh
