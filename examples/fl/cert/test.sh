# medperf mlcube run_test --container $PWD/mlcube/mlcube.yaml --task get_client_cert -e MEDPERF_INPUT_CN=hasan.kassem@mlcommons.org --allow_network
# medperf mlcube run_test --container $PWD/mlcube/mlcube.yaml --task get_server_cert -e MEDPERF_INPUT_CN=34.41.173.238 -P 80 
# medperf mlcube run --mlcube ./mlcube --task get_server_cert
# medperf mlcube run_test --container $PWD/mlcube/mlcube.yaml --task trust --allow_network
medperf mlcube run_test --container $PWD/mlcube/mlcube.yaml --task verify_cert -e MEDPERF_INPUT_CN=hasan.kassem@mlcommons.org --allow_network
