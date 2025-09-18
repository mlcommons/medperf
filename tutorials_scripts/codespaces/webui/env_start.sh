#!/usr/bin/env bash
echo "Preparing local medperf server..."
# we are located at /workspaces/medperf/ where repo is cloned to
pip install -e ./cli
pip install -r server/requirements.txt
pip install -r server/test-requirements.txt
medperf profile activate local

bash tutorials_scripts/setup_webui_tutorial.sh
cd server
cp .env.local.local-auth.sqlite .env

echo "Medperf is ready for local usage"
cd ..
