#!/usr/bin/env bash
cd /workspaces/medperf/server
bash ./setup-dev-server.sh < /dev/null &>server.log &
