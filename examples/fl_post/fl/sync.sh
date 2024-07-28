cp mlcube/workspace/training_config.yaml mlcube_agg/workspace/training_config.yaml

cp mlcube/mlcube.yaml mlcube_agg/mlcube.yaml
cp mlcube/mlcube.yaml mlcube_col1/mlcube.yaml
cp mlcube/mlcube.yaml mlcube_col2/mlcube.yaml
cp mlcube/mlcube.yaml mlcube_col3/mlcube.yaml

rm -r mlcube_col1/workspace/additional_files
rm -r mlcube_col2/workspace/additional_files
rm -r mlcube_col3/workspace/additional_files

cp -r mlcube/workspace/additional_files mlcube_col1/workspace/additional_files
cp -r mlcube/workspace/additional_files mlcube_col2/workspace/additional_files
cp -r mlcube/workspace/additional_files mlcube_col3/workspace/additional_files
