medperf mlcube run --mlcube ./mlcube --task get_client_cert -e MEDPERF_INPUT_CN=hasan.kassem@mlcommons.org
medperf mlcube run --mlcube ./mlcube --task get_server_cert -e MEDPERF_INPUT_CN=34.41.173.238 -P 80
# medperf mlcube run --mlcube ./mlcube --task get_server_cert
medperf mlcube run --mlcube ./mlcube --task trust
# docker run -it --entrypoint=/bin/bash --env MEDPERF_INPUT_CN=col1@example.com --volume '/home/hasan/work/medperf_ws/medperf/examples/fl/cert/mlcube/workspace:/mlcube_io0:ro' --volume '/home/hasan/work/medperf_ws/medperf/examples/fl/cert/mlcube/workspace/pki_assets:/mlcube_io1' mlcommons/medperf-step-cli:0.0.0
# bash /mlcube_project/get_cert.sh get_client_cert --ca_config=/mlcube_io0/ca_config.json --pki_assets=/mlcube_io1
