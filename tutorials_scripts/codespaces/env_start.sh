#!/usr/bin/env bash
echo "Preparing local medperf server..."
# we are located at /workspaces/medperf/ where repo is cloned to
pip install -r server/requirements.txt
pip install -r server/test-requirements.txt
pip install -e ./cc
pip install -e ./cli
medperf profile activate local

cd server
cp .env.local.local-auth.sqlite .env
medperf auth login -e testmo@example.com
echo "Medperf is ready for local usage"
cd ..
