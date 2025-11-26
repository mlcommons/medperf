$DIR=$(dirname "$0")
medperf container run_test --container ./container_config.yaml \
    --task trust \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"

medperf container run_test --container ./container_config.yaml \
    --task get_client_cert -e MEDPERF_INPUT_CN=hasan.kassem@mlcommons.org \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"


medperf container run_test --container ./container_config.yaml \
    --task get_server_cert -e MEDPERF_INPUT_CN=34.41.173.238 -P 80 \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"

medperf container run_test --container ./container_config.yaml \
    --task verify_cert -e MEDPERF_INPUT_CN=hasan.kassem@mlcommons.org \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"