from utils import (
    get_collaborator_cn,
    prepare_node_cert,
    prepare_ca_cert,
    prepare_plan,
    prepare_data,
    WORKSPACE,
)
import os
from subprocess import check_call


def start_collaborator(
    data_path,
    labels_path,
    parameters_file,
    node_cert_folder,
    ca_cert_folder,
    network_config,
    output_logs,  # TODO: Is it needed?
):
    prepare_plan(parameters_file, network_config)
    cn = get_collaborator_cn()
    prepare_node_cert(node_cert_folder, "client", f"col_{cn}")
    prepare_ca_cert(ca_cert_folder)
    prepare_data(data_path, labels_path, cn)

    # set log files
    check_call(["fx", "collaborator", "start", "-n", cn], cwd=WORKSPACE)
