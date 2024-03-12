from utils import (
    get_aggregator_fqdn,
    prepare_node_cert,
    prepare_ca_cert,
    prepare_plan,
    prepare_cols_list,
    prepare_init_weights,
    create_workspace,
    get_weights_path,
)

import os
import shutil
from subprocess import check_call
from distutils.dir_util import copy_tree


def start_aggregator(
    input_weights,
    parameters_file,
    node_cert_folder,
    ca_cert_folder,
    output_logs,
    output_weights,
    network_config,
    collaborators,
):

    workspace_folder = os.path.join(output_logs, "workspace")
    create_workspace(workspace_folder)
    prepare_plan(parameters_file, network_config, workspace_folder)
    prepare_cols_list(collaborators, workspace_folder)
    prepare_init_weights(input_weights, workspace_folder)
    fqdn = get_aggregator_fqdn(workspace_folder)
    prepare_node_cert(node_cert_folder, "server", f"agg_{fqdn}", workspace_folder)
    prepare_ca_cert(ca_cert_folder, workspace_folder)

    check_call(["fx", "aggregator", "start"], cwd=workspace_folder)

    # TODO: check how to copy logs during runtime.
    #       perhaps investigate overriding plan entries?

    # NOTE: logs and weights are copied, even if target folders are not empty
    copy_tree(os.path.join(workspace_folder, "logs"), output_logs)

    # NOTE: conversion fails since openfl needs sample data...
    # weights_paths = get_weights_path(fl_workspace)
    # out_best = os.path.join(output_weights, "best")
    # out_last = os.path.join(output_weights, "last")
    # check_call(
    #     ["fx", "model", "save", "-i", weights_paths["best"], "-o", out_best],
    #     cwd=workspace_folder,
    # )
    copy_tree(os.path.join(workspace_folder, "save"), output_weights)

    # Cleanup
    shutil.rmtree(workspace_folder, ignore_errors=True)
