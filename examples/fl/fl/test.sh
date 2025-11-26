# generate plan and copy it to each node
medperf container run_test --container ./workspace_agg --task generate_plan
mv ./workspace_agg/plan/plan.yaml ./workspace_agg/workspace
rm -r ./workspace_agg/plan
cp ./workspace_agg/plan.yaml ./workspace_col1/
cp ./workspace_agg/plan.yaml ./workspace_col2/
cp ./workspace_agg/plan.yaml ./workspace_col3/
cp ./workspace_agg/plan.yaml ./for_admin

# Run nodes
# TODO: put mounts according to container_config.yaml
AGG="medperf container run_test --container ./container_config.yaml --task start_aggregator -P 50273"
COL1="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col1@example.com"
COL2="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col2@example.com"
COL3="medperf container run_test --container ./container_config.yaml --task train -e MEDPERF_PARTICIPANT_LABEL=col3@example.com"

# gnome-terminal -- bash -c "$AGG; bash"
# gnome-terminal -- bash -c "$COL1; bash"
# gnome-terminal -- bash -c "$COL2; bash"
# gnome-terminal -- bash -c "$COL3; bash"
rm agg.log col1.log col2.log col3.log
$AGG >>agg.log &
sleep 6
$COL1 >>col1.log &
sleep 6
$COL2 >>col2.log &
sleep 6
$COL3 >>col3.log &
wait
