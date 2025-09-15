mkdir -p /tmp/provision
cp /mlcommons/volumes/training_config/secure_project.yml /tmp/provision/secure_project.yml
cd /tmp/provision
nvflare provision -p ./secure_project.yml
python3 /project/generate_plan.py