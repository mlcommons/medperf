cp -r ./workspace ./workspace_admin

# Get your node cert folder and ca cert folder from the aggregator setup. Modify paths as needed.
cp -r ../fl/for_admin/node_cert ./workspace_admin/node_cert
cp -r ../fl/for_admin/ca_cert ./workspace_admin/ca_cert

# Note that you should use the same plan used in the federation
cp ../fl/for_admin/plan.yaml ./workspace_admin/plan.yaml