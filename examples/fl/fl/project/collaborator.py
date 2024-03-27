from utils import (
    get_collaborator_cn,
    prepare_node_cert,
    prepare_ca_cert,
    prepare_plan,
    create_workspace,
)
import os
import shutil
from subprocess import check_call


def start_collaborator(
    data_path,
    labels_path,
    parameters_file,
    node_cert_folder,
    ca_cert_folder,
    network_config,
    output_logs,
):
    workspace_folder = os.path.join(output_logs, "workspace")
    create_workspace(workspace_folder)
    prepare_plan(parameters_file, network_config, workspace_folder)
    cn = get_collaborator_cn()
    prepare_node_cert(node_cert_folder, "client", f"col_{cn}", workspace_folder)
    prepare_ca_cert(ca_cert_folder, workspace_folder)

    # set log files
    check_call(["fx", "collaborator", "start", "-n", cn], cwd=workspace_folder)

    # Cleanup
    shutil.rmtree(workspace_folder, ignore_errors=True)
