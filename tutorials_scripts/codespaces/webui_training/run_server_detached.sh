#!/usr/bin/env bash
cd /workspaces/medperf/server
bash ./setup-dev-server.sh < /dev/null &>server.log &
sleep 10

docker pull mlcommons/chestxray-tutorial-prep:0.0.1
docker pull mlcommons/medperf-flower-fl:1.0.0

python seed.py --demo tutorial
cd ..
# Create three instances of web UI

mkdir -p /workspaces/.medperf_config1
mkdir -p /workspaces/.medperf_config2
mkdir -p /workspaces/.medperf_config3

MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf profile activate local
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf profile activate local
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf profile activate local


MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf auth login -e testmo@example.com
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf auth login -e testdo@example.com
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf auth login -e testdo2@example.com

MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf_webui --port 8001 &>/dev/null &
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf_webui --port 8002 &>/dev/null &
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf_webui --port 8003 &>/dev/null &

URL1=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')
URL2=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')
URL3=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')

echo "Medperf is ready for local usage"

echo "Access Model Owner Web UI at $URL1"
echo "Access Data Owner 1 Web UI at $URL2"
echo "Access Data Owner 2 Web UI at $URL3"
echo "Use the following address when registering the aggregator: $(hostname -I | cut -d " " -f 1)"