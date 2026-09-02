#!/usr/bin/env bash
cd /workspaces/medperf/server
python -m medperf_server start < /dev/null &>server.log &
