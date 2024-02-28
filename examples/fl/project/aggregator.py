from utils import (
    get_aggregator_fqdn,
    prepare_node_cert,
    prepare_ca_cert,
    prepare_plan,
    prepare_cols_list,
    prepare_init_weights,
    get_weights_path,
    WORKSPACE,
)

import os
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
    prepare_plan(parameters_file, network_config)
    prepare_cols_list(collaborators)
    prepare_init_weights(input_weights)
    fqdn = get_aggregator_fqdn()
    prepare_node_cert(node_cert_folder, "server", f"agg_{fqdn}")
    prepare_ca_cert(ca_cert_folder)

    check_call(["fx", "aggregator", "start"], cwd=WORKSPACE)

    # TODO: check how to copy logs during runtime.
    #       perhaps investigate overriding plan entries?

    # NOTE: logs and weights are copied, even if target folders are not empty
    copy_tree(os.path.join(WORKSPACE, "logs"), output_logs)

    # NOTE: conversion fails since openfl needs sample data...
    # weights_paths = get_weights_path()
    # out_best = os.path.join(output_weights, "best")
    # out_last = os.path.join(output_weights, "last")
    # check_call(
    #     ["fx", "model", "save", "-i", weights_paths["best"], "-o", out_best],
    #     cwd=WORKSPACE,
    # )
    copy_tree(os.path.join(WORKSPACE, "save"), output_weights)
