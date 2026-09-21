# Runs this container's `prepare` then `statistics` tasks locally against the
# data under ./workspace. See README.md ("How to test") for what needs to go
# there (real DICOM data — not provided in this repo), and edit the --mounts
# paths below to point at your own data.
DIR=$(dirname "$(realpath "$0")")

medperf container run_test --container "$DIR/container_config.yaml" \
    --task prepare \
    --parameters_file_path "$DIR/workspace/parameters.yaml" \
    --additional_files_path "$DIR/workspace/additional_files" \
    -o "$DIR/logs_prepare.log" \
    --mounts "data_path=$DIR/workspace/input_data,labels_path=$DIR/workspace/input_labels,output_path=$DIR/workspace/data,output_labels_path=$DIR/workspace/labels,metadata_path=$DIR/workspace/metadata,report_file=$DIR/workspace/report.yaml"

medperf container run_test --container "$DIR/container_config.yaml" \
    --task statistics \
    --parameters_file_path "$DIR/workspace/parameters.yaml" \
    -o "$DIR/logs_statistics.log" \
    --mounts "data_path=$DIR/workspace/data,labels_path=$DIR/workspace/labels,output_path=$DIR/workspace/statistics.yaml"
