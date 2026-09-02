#!/usr/bin/env bash
echo "Preparing local medperf server..."
# we are located at /workspaces/medperf/ where repo is cloned to
pip install -r server/requirements.txt -r server/test-requirements.txt
pip install -e ./cli
medperf profile activate local

cd server
python -m medperf_server set_config sqlite
medperf auth login -e testmo@example.com
echo "Medperf is ready for local usage"
cd ..
