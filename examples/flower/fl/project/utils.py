import yaml
from distutils.dir_util import copy_tree
import os
import tomllib
import tomli_w


def get_train_val_paths(data_path, labels_path):
    return data_path, labels_path, data_path, labels_path


def get_server_connection(plan_path):
    with open(plan_path) as f:
        plan = yaml.safe_load(f)
    address = plan["aggregator"]["address"]
    port = plan["aggregator"]["port"]
    admin_port = plan["aggregator"]["admin_port"]
    return address, port, admin_port


def setup_job(src_folder, plan_path):
    workspace_folder = "/tmp/flwr_ws"
    copy_tree(src_folder, workspace_folder)
    toml_template = os.path.join(workspace_folder, "pyproject_tpl.toml")
    with open(toml_template, "rb") as f:
        toml_config = tomllib.load(f)
    with open(plan_path) as f:
        plan = yaml.safe_load(f)
    toml_config["tool"]["flwr"]["app"]["config"] = plan["config"]
    address, _, admin_port = get_server_connection(plan_path)
    toml_config["tool"]["flwr"]["federations"]["medperf-deployment"][
        "address"
    ] = f"{address}:{admin_port}"
    toml_file = os.path.join(workspace_folder, "pyproject.toml")

    with open(toml_file, "w") as f:
        f.write(tomli_w.dumps(toml_config))
    return workspace_folder
