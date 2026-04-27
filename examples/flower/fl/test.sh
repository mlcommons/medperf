# generate plan and copy it to each node
source ./.env
AGG_PATH=/home/hasan/work/medperf_ws/medperf/examples/flower/fl/workspace_agg
arg1="aggregator_config_path=$AGG_PATH/aggregator_config.yaml"
arg2="training_config_path=$AGG_PATH/training_config.yaml"
arg3="plan_path=$AGG_PATH/plan.yaml"

medperf container run_test --container ./container_config.yaml --task generate_plan \
    --mounts "$arg1,$arg2,$arg3"

cp $AGG_PATH/plan.yaml ./for_admin

arg1="ca_cert_folder=$AGG_PATH/ca_cert"
arg2="node_cert_folder=$AGG_PATH/node_cert"
arg3="collaborators=$AGG_PATH/cols.yaml"
arg4="plan_path=$AGG_PATH/plan.yaml"
arg5="output_logs=$AGG_PATH/logs"
arg6="output_weights=$AGG_PATH/final_weights"
arg7="report_path=$AGG_PATH/report.yaml"
mkdir -p $AGG_PATH/logs
mkdir -p $AGG_PATH/final_weights

# Run nodes
AGG_MOUNTS="$arg1,$arg2,$arg3,$arg4,$arg5,$arg6,$arg7"
AGG="medperf container run_test --container ./container_config.yaml --task start_aggregator -P "$HOSTNAME_:$PORT_:$PORT_,$HOSTNAME_:$ADMIN_PORT_:$ADMIN_PORT_" --additional_files_path $AGG_PATH/additional_files --mounts $AGG_MOUNTS --allow_network"


COL_PATH=/home/hasan/work/medperf_ws/medperf/examples/flower/fl/workspace_col1
arg1="ca_cert_folder=$COL_PATH/ca_cert"
arg2="node_cert_folder=$COL_PATH/node_cert"
arg3="data_path=$COL_PATH/data"
arg4="plan_path=$AGG_PATH/plan.yaml"
arg5="output_logs=$COL_PATH/logs"
arg6="labels_path=$COL_PATH/labels"
mkdir -p $COL_PATH/logs
COL_MOUNTS="$arg1,$arg2,$arg3,$arg4,$arg5,$arg6"
COL1="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col1@example.com --mounts $COL_MOUNTS --allow_network"

COL_PATH=/home/hasan/work/medperf_ws/medperf/examples/flower/fl/workspace_col2
arg1="ca_cert_folder=$COL_PATH/ca_cert"
arg2="node_cert_folder=$COL_PATH/node_cert"
arg3="data_path=$COL_PATH/data"
arg4="plan_path=$AGG_PATH/plan.yaml"
arg5="output_logs=$COL_PATH/logs"
arg6="labels_path=$COL_PATH/labels"
mkdir -p $COL_PATH/logs
COL_MOUNTS="$arg1,$arg2,$arg3,$arg4,$arg5,$arg6"

COL2="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col2@example.com --mounts $COL_MOUNTS --allow_network"

COL_PATH=/home/hasan/work/medperf_ws/medperf/examples/flower/fl/workspace_col3
arg1="ca_cert_folder=$COL_PATH/ca_cert"
arg2="node_cert_folder=$COL_PATH/node_cert"
arg3="data_path=$COL_PATH/data"
arg4="plan_path=$AGG_PATH/plan.yaml"
arg5="output_logs=$COL_PATH/logs"
arg6="labels_path=$COL_PATH/labels"
mkdir -p $COL_PATH/logs
COL_MOUNTS="$arg1,$arg2,$arg3,$arg4,$arg5,$arg6"
COL3="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col3@example.com --mounts $COL_MOUNTS --allow_network"

# gnome-terminal -- bash -c "$AGG; bash"
# gnome-terminal -- bash -c "$COL1; bash"
# gnome-terminal -- bash -c "$COL2; bash"
# gnome-terminal -- bash -c "$COL3; bash"
rm agg.log col1.log col2.log col3.log
$AGG >>agg.log &
sleep 20
$COL1 >>col1.log &
sleep 6
$COL2 >>col2.log &
sleep 6
$COL3 >>col3.log &
wait
