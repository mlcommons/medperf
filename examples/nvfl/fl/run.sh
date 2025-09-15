rm col1.log
rm col2.log
rm agg.log

docker container stop col1
docker container stop col2
docker container stop agg
docker container prune -f

cd node
sh build.sh
cd ../admin
sh build.sh
cd ..


rm -rf agg
rm -rf admink
rm -rf col1
rm -rf col2
rm -rf $PWD/kits
rm -rf $PWD/plan.yaml
rm -rf $PWD/metadata.yaml
rm -rf $PWD/status.yaml
rm -rf $PWD/output_weights

mkdir $PWD/kits
mkdir $PWD/output_weights
touch $PWD/plan.yaml
touch $PWD/metadata.yaml
touch $PWD/status.yaml


docker run -u 1000:1000 --env MEDPERF_PARTICIPANT_LABEL=testmo@example.com \
    --volume $PWD/plan.yaml:/mlcommons/volumes/plan/plan.yaml \
    --volume $PWD/kits:/mlcommons/volumes/kits \
    --volume $PWD/metadata.yaml:/mlcommons/volumes/kits_meta/metadata.yaml \
    --volume $PWD/node/workspace/training_config:/mlcommons/volumes/training_config \
    --volume $PWD/node/workspace/aggregator_config.yaml:/mlcommons/volumes/aggregator_config \
    mlcommons/medperf-nv-node:1.0.0 bash /project/generate_plan.sh

mkdir agg
tar -xf kits/192.168.1.223.tar.gz -C agg

mkdir admink
tar -xf kits/testmo@example.com.tar.gz -C admink

mkdir col1
tar -xf kits/col1-example-com.tar.gz -C col1

mkdir col2
tar -xf kits/col2-example-com.tar.gz -C col2
##

docker run --rm -d --name agg -u 1000:1000 -p 192.168.1.223:8102:8102 -p 192.168.1.223:8103:8103 \
    --volume $PWD/agg:/mlcommons/volumes/fl_workspace \
    mlcommons/medperf-nv-node:1.0.0 bash /project/entrypoint.sh

docker logs -f agg &> agg.log &

sleep 20

docker run -u 1000:1000 --env MEDPERF_PARTICIPANT_LABEL=testmo@example.com \
    --volume $PWD/admink:/mlcommons/volumes/fl_workspace \
    --volume $PWD/plan.yaml:/mlcommons/volumes/plan/plan.yaml \
    mlcommons/medperf-nv-admin:1.0.0 bash /project/entrypoint_submit.sh


docker run --rm -d --name col1 -u 1000:1000 \
    --volume /home/hasan/work/medperf_ws/nvflare/data/col1/data:/mlcommons/volumes/data \
    --volume /home/hasan/work/medperf_ws/nvflare/data/col1/labels:/mlcommons/volumes/labels \
    --volume $PWD/col1:/mlcommons/volumes/fl_workspace \
    mlcommons/medperf-nv-node:1.0.0 bash /project/entrypoint.sh

docker logs -f col1 &> col1.log &

docker run --rm -d --name col2 -u 1000:1000 \
    --volume /home/hasan/work/medperf_ws/nvflare/data/col2/data:/mlcommons/volumes/data \
    --volume /home/hasan/work/medperf_ws/nvflare/data/col2/labels:/mlcommons/volumes/labels \
    --volume $PWD/col2:/mlcommons/volumes/fl_workspace \
    mlcommons/medperf-nv-node:1.0.0 bash /project/entrypoint.sh

docker logs -f col2 &> col2.log &


# docker run -u 1000:1000 --env MEDPERF_PARTICIPANT_LABEL=testmo@example.com \
#     --volume $PWD/admink:/mlcommons/volumes/fl_workspace \
#     --volume $PWD/status.yaml:/mlcommons/volumes/status/status.yaml \
#     mlcommons/medperf-nv-admin:1.0.0 bash /project/entrypoint_get_status.sh


# docker run -u 1000:1000 --env MEDPERF_PARTICIPANT_LABEL=testmo@example.com \
#     --volume $PWD/admink:/mlcommons/volumes/fl_workspace \
#     --volume $PWD/output_weights:/mlcommons/volumes/output_weights \
#     mlcommons/medperf-nv-admin:1.0.0 bash /project/entrypoint_stop.sh


