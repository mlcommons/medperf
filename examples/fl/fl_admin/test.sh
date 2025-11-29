# Make sure an aggregator is up somewhere, and it is configured to
# accept admin@example.com as an admin and to allow any endpoints you are willing to test

# Uncommend and test

DIR=$(dirname "$(realpath "$0")")
# GET EXPERIMENT STATUS
env_arg1="MEDPERF_ADMIN_PARTICIPANT_CN=col1@example.com"

mount_arg1="output_status_file=$DIR/workspace_admin/status/status.yaml"
mount_arg2="ca_cert_folder=$DIR/workspace_admin/ca_cert"
mount_arg3="node_cert_folder=$DIR/workspace_admin/node_cert"
mount_arg4="plan_path=$DIR/workspace_admin/plan.yaml"
mounts="$mount_arg1,$mount_arg2,$mount_arg3,$mount_arg4"
env_args=$env_arg1
medperf container run_test ./container_config.yaml --task get_experiment_status \
    -e $env_args --mounts "$mounts"

# SET STRAGGLER CUTOFF
env_arg1="MEDPERF_ADMIN_PARTICIPANT_CN=admin@example.com"
env_arg2="MEDPERF_UPDATE_FIELD_NAME=straggler_handling_policy.settings.straggler_cutoff_time"
env_arg3="MEDPERF_UPDATE_FIELD_VALUE=1200"

mount_arg1="ca_cert_folder=$DIR/workspace_admin/ca_cert"
mount_arg2="node_cert_folder=$DIR/workspace_admin/node_cert"
mount_arg3="plan_path=$DIR/workspace_admin/plan.yaml"
mounts="$mount_arg1,$mount_arg2,$mount_arg3"
env_args="$env_arg1,$env_arg2,$env_arg3"
medperf container run_test ./container_config.yaml --task update_plan \
    -e $env_args --mounts "$mounts"

# SET DYNAMIC TASK ARG
env_arg1="MEDPERF_ADMIN_PARTICIPANT_CN=col1@example.com"
env_arg2="MEDPERF_UPDATE_FIELD_NAME=dynamictaskargs.train.train_cutoff_time"
env_arg3="MEDPERF_UPDATE_FIELD_VALUE=20"

mount_arg1="ca_cert_folder=$DIR/workspace_admin/ca_cert"
mount_arg2="node_cert_folder=$DIR/workspace_admin/node_cert"
mount_arg3="plan_path=$DIR/workspace_admin/plan.yaml"
mounts="$mount_arg1,$mount_arg2,$mount_arg3"
env_args="$env_arg1,$env_arg2,$env_arg3"

medperf container run_test ./container_config.yaml --task update_plan \
    -e $env_args --mounts "$mounts"
