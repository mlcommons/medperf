DATA_PATH=/tmp/medperf_tests_20260222031259/storage/data/localhost_8000/c86149a1f5cc0af3a78069c80c080147580e1c0b55ee3870e6e5633a95309cde/data
LABELS_PATH=/tmp/medperf_tests_20260222031259/storage/data/localhost_8000/c86149a1f5cc0af3a78069c80c080147580e1c0b55ee3870e6e5633a95309cde/labels
MODEL=/home/hasan/work/medperf_ws/medperf/medperf_tutorial/model_custom_cnn/workspace/additional_files
RES=/home/hasan/work/medperf_ws/medperf/medperf_tutorial/tmppp
mkdir -p $RES
medperf container run_test --container ./container_config.yaml --task run_script --env MEDPERF_ON_PREM=1 \
    --mounts "data_path=$DATA_PATH,labels_path=$LABELS_PATH,model_files=$MODEL,results_path=$RES"