#!/usr/bin/env bash
cd /workspaces/medperf/server
bash ./setup-dev-server.sh < /dev/null &>server.log &

docker pull mlcommons/chestxray-tutorial-prep:0.0.1
docker pull mlcommons/chestxray-tutorial-metrics:0.0.1
docker pull mlcommons/chestxray-tutorial-cnn:0.0.1
docker pull mlcommons/chestxray-tutorial-mobilenetv2:0.0.1