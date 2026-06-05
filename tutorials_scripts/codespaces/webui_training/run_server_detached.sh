#!/usr/bin/env bash
cd /workspaces/medperf/server
bash ./setup-dev-server.sh < /dev/null &>server.log &
sleep 10

docker pull mlcommons/chestxray-tutorial-prep:0.0.1
docker pull mlcommons/medperf-flower-fl:1.0.0

python seed.py --demo tutorial &>/dev/null
cd ..
# Create three instances of web UI
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf_webui --port 8001 &>/dev/null &
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf_webui --port 8002 &>/dev/null &
MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf_webui --port 8003 &>/dev/null &

URL1=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config1 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')
URL2=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config2 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')
URL3=$(MEDPERF_CONFIG_STORAGE=/workspaces/.medperf_config3 medperf get_webui_properties 2>/dev/null | grep -oP 'http://\S+')


echo ""
echo "========================================"
echo "Access Model Owner Web UI at:"
echo "    $URL1"
echo ""
echo "Access Data Owner 1 Web UI at:"
echo "    $URL2"
echo ""
echo "Access Data Owner 2 Web UI at:"
echo "    $URL3"
echo "========================================"
echo ""
echo "Use the following address when registering the aggregator: $(hostname -I | cut -d " " -f 1)"
echo "========================================"
echo "Medperf is ready for local usage"
