#!/usr/bin/env bash
cd /workspaces/medperf/server
bash ./setup-dev-server.sh < /dev/null &>server.log &

docker pull mlcommons/chestxray-tutorial-prep:0.0.1
docker pull mlcommons/medperf-nv-admin:1.0.0
docker pull mlcommons/medperf-nv-node:1.0.0

sleep 10
python seed.py --demo benchmark
echo "Medperf is ready for local usage"