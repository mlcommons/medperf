DIR=$(dirname "$(realpath "$0")")

medperf container run_test --container ./container_config.yaml \
    --task trust \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"
sh clean.sh
medperf container run_test --container ./container_config.yaml \
    --task get_client_cert -e MEDPERF_INPUT_CN=user@example.com \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"
sh clean.sh
medperf container run_test --container ./container_config.yaml \
    --task get_server_cert -e MEDPERF_INPUT_CN=https://example.com \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"
sh clean.sh
medperf container run_test --container ./container_config.yaml \
    --task verify_cert -e MEDPERF_INPUT_CN=user@example.com \
    --mounts "ca_config=$DIR/workspace/ca_config.json,pki_assets=$DIR/workspace/pki_assets"