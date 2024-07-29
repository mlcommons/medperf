cp -r ./mlcube ./mlcube_admin

# Get your node cert folder and ca cert folder from the aggregator setup. Modify paths as needed.
cp -r ../fl/for_admin/node_cert ./mlcube_admin/node_cert
cp -r ../fl/for_admin/ca_cert ./mlcube_admin/ca_cert

# Note that you should use the same plan used in the federation
# cp ../fl/for_admin/plan.yaml ./mlcube_admin/workspace/plan.yaml
