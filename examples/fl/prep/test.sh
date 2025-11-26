DIR=$(dirname "$(realpath "$0")")
medperf container run --container ./container_config.yaml \
    --task prepare \
    -o ./logs_prep.log \
    --mounts "data_path=$DIR/workspace/input_data,labels_path=$DIR/workspace/input_labels,output_path=$DIR/workspace/prepared_data,output_labels_path=$DIR/workspace/prepared_labels"
medperf container run --container ./container_config.yaml \
    --task sanity_check \
    -o ./logs_sanity.log \
    --mounts "data_path=$DIR/workspace/prepared_data,labels_path=$DIR/workspace/prepared_labels"
medperf container run --container ./container_config.yaml \
    --task statistics \
    -o ./logs_stats.log \
    --mounts "data_path=$DIR/workspace/prepared_data,labels_path=$DIR/workspace/prepared_labels,output_path=$DIR/workspace/statistics/statistics.yaml"
