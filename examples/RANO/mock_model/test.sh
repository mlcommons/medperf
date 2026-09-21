# Runs this container's `infer` task locally against ./workspace/input_data.
# See README.md for what needs to go there. Edit the --mounts paths below to
# point at your own data.
DIR=$(dirname "$(realpath "$0")")

medperf container run_test --container "$DIR/container_config.yaml" \
    --task infer \
    -o "$DIR/logs_infer.log" \
    --mounts "data_path=$DIR/workspace/input_data,output_path=$DIR/workspace/predictions"
