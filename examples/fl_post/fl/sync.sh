cp mlcube/workspace/training_config.yaml mlcube_agg/workspace/training_config.yaml
cp mlcube/mlcube.yaml mlcube_agg/mlcube.yaml

for dir in mlcube_col*/; do
    if [ -d "$dir" ]; then
        cp mlcube/mlcube.yaml $dir/mlcube.yaml
        rm -r $dir/workspace/additional_files
        cp -r mlcube/workspace/additional_files $dir/workspace/additional_files
    fi
done
