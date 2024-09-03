import os
import shutil
from subprocess import check_call
from distutils.dir_util import copy_tree


def start_aggregator(workspace_folder, output_logs, output_weights, report_path):

    check_call(["fx", "aggregator", "start"], cwd=workspace_folder)

    # TODO: check how to copy logs during runtime.
    #       perhaps investigate overriding plan entries?

    # NOTE: logs and weights are copied, even if target folders are not empty
    if os.path.exists(os.path.join(workspace_folder, "logs")):
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

    with open(report_path, "w") as f:
        f.write("IsDone: 1")
