export HTTPS_PROXY=
export http_proxy=

# generate plan and copy it to each node
GENERATE_PLAN_PLATFORM="docker"
AGG_PLATFORM="docker"
COL1_PLATFORM="singularity"
COL2_PLATFORM="docker"
COL3_PLATFORM="docker"

medperf --platform $GENERATE_PLAN_PLATFORM mlcube run --mlcube ./mlcube_agg --task generate_plan
mv ./mlcube_agg/workspace/plan/plan.yaml ./mlcube_agg/workspace
rm -r ./mlcube_agg/workspace/plan
cp ./mlcube_agg/workspace/plan.yaml ./mlcube_col1/workspace
cp ./mlcube_agg/workspace/plan.yaml ./mlcube_col2/workspace
cp ./mlcube_agg/workspace/plan.yaml ./mlcube_col3/workspace
cp ./mlcube_agg/workspace/plan.yaml ./for_admin

# Run nodes
AGG="medperf --platform $AGG_PLATFORM mlcube run --mlcube ./mlcube_agg --task start_aggregator -P 50273"
COL1="medperf --platform $COL1_PLATFORM --gpus=1 mlcube run --mlcube ./mlcube_col1 --task train -e MEDPERF_PARTICIPANT_LABEL=col1@example.com"
COL2="medperf --platform $COL2_PLATFORM --gpus=device=2 mlcube run --mlcube ./mlcube_col2 --task train -e MEDPERF_PARTICIPANT_LABEL=col2@example.com"
COL3="medperf --platform $COL3_PLATFORM --gpus=device=1 mlcube run --mlcube ./mlcube_col3 --task train -e MEDPERF_PARTICIPANT_LABEL=col3@example.com"

# medperf --gpus=device=2 mlcube run --mlcube ./mlcube_col1 --task train -e MEDPERF_PARTICIPANT_LABEL=col1@example.com >>col1.log &

# gnome-terminal -- bash -c "$AGG; bash"
# gnome-terminal -- bash -c "$COL1; bash"
# gnome-terminal -- bash -c "$COL2; bash"
# gnome-terminal -- bash -c "$COL3; bash"
rm agg.log col1.log col2.log col3.log
$AGG >>agg.log &
sleep 6
$COL2 >>col2.log &
sleep 6
$COL3 >>col3.log &
# sleep 6
# $COL2 >> col2.log &
# sleep 6
# $COL3 >> col3.log &
wait

# docker run --env MEDPERF_PARTICIPANT_LABEL=col1@example.com --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace/data:/mlcube_io0:ro --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace/labels:/mlcube_io1:ro --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace/node_cert:/mlcube_io2:ro --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace/ca_cert:/mlcube_io3:ro --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace:/mlcube_io4:ro --volume /home/hasan/work/medperf_ws/medperf/examples/fl/fl/mlcube_col1/workspace/logs:/mlcube_io5 -it --entrypoint bash mlcommons/medperf-fl:1.0.0
# python /mlcube_project/mlcube.py train --data_path=/mlcube_io0 --labels_path=/mlcube_io1 --node_cert_folder=/mlcube_io2 --ca_cert_folder=/mlcube_io3 --plan_path=/mlcube_io4/plan.yaml --output_logs=/mlcube_io5
