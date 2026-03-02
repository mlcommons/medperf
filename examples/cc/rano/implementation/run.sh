DATA_PATH=/home/hasan_kassem/rano_data/testdata/data
LABELS_PATH=/home/hasan_kassem/rano_data/testdata/labels
MODEL=/home/hasan_kassem/additional_files
RES=/home/hasan_kassem/rano_data/tmppp_results
rm -rf $RES
mkdir -p $RES
GPUS="0"
medperf --gpus=$GPUS container run_test --container ./container_config.yaml --task run_script --env MEDPERF_ON_PREM=1 \
    --mounts "data_path=$DATA_PATH,labels_path=$LABELS_PATH,model_files=$MODEL,results_path=$RES"
