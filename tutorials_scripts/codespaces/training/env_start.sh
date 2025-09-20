#!/usr/bin/env bash
echo "Preparing local medperf server..."
# we are located at /workspaces/medperf/ where repo is cloned to
pip install -e ./cli
pip install -r server/requirements.txt
pip install -r server/test-requirements.txt
medperf profile activate local

bash tutorials_scripts/setup_training_tutorial.sh

# Update the configured server ip address
sed -i "s/^  - name: 192.*/  - name: $(hostname -I | cut -d' ' -f 1)/" medperf_tutorial/training_config/secure_project.yml

cd server
cp .env.local.local-auth.sqlite .env
cd ..
