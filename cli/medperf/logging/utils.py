import logging
import traceback
import os
import platform
import re
import socket
import subprocess
import sys
import tarfile
from importlib import metadata

import psutil
import yaml

from medperf import config


def get_system_information():
    # Get basic system information
    system_info = {
        "Platform": platform.platform(),
        "Hostname": socket.gethostname(),
        "Processor": platform.processor(),
        "System Version": platform.version(),
        "Python Version": platform.python_version(),
    }
    return system_info


def get_memory_usage():
    # Get memory usage
    memory = psutil.virtual_memory()
    return {
        "Total Memory": memory.total,
        "Available Memory": memory.available,
        "Used Memory": memory.used,
        "Memory Usage Percentage": memory.percent,
    }


def get_disk_usage():
    # Get disk usage
    paths_of_interest = [os.environ["HOME"], config.config_storage]
    disk_usage_dict = {}
    for poi in paths_of_interest:
        try:
            disk_usage_poi = psutil.disk_usage(poi)
        except OSError:
            disk_usage_poi = "NOT FOUND"
        disk_usage_dict[poi] = {
            "Total Disk Space": disk_usage_poi.total,
            "Used Disk Space": disk_usage_poi.used,
            "Free Disk Space": disk_usage_poi.free,
            "Disk Usage Percentage": disk_usage_poi.percent,
        }

    return disk_usage_dict


def get_configuration_variables():
    config_vars = vars(config)
    config_dict = {}
    for item in dir(config):
        if item.startswith("__"):
            continue
        config_dict[item] = config_vars[item]
    config_dict = filter_var_dict_for_yaml(config_dict)
    return config_dict


def filter_var_dict_for_yaml(unfiltered_dict):
    valid_types = (str, dict, list, int, float)
    filtered_dict = {}
    for key, value in unfiltered_dict.items():
        if not isinstance(value, valid_types) and value is not None:
            try:
                value = str(value)
            except Exception:
                value = "<OBJECT>"
        if isinstance(value, dict):
            value = filter_var_dict_for_yaml(value)
        filtered_dict[key] = value

    return filtered_dict


def get_storage_contents():
    storage_paths = config.storage.copy()
    storage_paths["credentials_folder"] = {
        "base": os.path.dirname(config.creds_folder),
        "name": os.path.basename(config.creds_folder),
    }
    ignore_paths = {"datasets_folder", "predictions_folder", "results_folder"}
    contents = {}

    for pathname, path in storage_paths.items():
        if pathname in ignore_paths:
            contents[pathname] = "<REDACTED>"
            continue
        full_path = os.path.join(path["base"], path["name"])
        p = subprocess.Popen(
            ["ls", "-lR", full_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output, _ = p.communicate()
        if p.returncode != 0:
            contents[pathname] = "Could not retrieve tree for storage paths"
        contents[pathname] = output

    return contents


def get_installed_packages():
    installed_packages = {}
    for dist in metadata.distributions():
        installed_packages[dist.name] = dist.version
    return installed_packages


def get_python_environment_information():
    environment_info = {
        "Operating System": platform.system(),
        "Operating System Release": platform.release(),
        "Operating System Version": platform.version(),
        "Python Implementation": platform.python_implementation(),
        "Python Version": platform.python_version(),
        "Python Compiler": platform.python_compiler(),
        "Python Build": platform.python_build(),
        "Machine Architecture": platform.machine(),
        "Processor Type": platform.processor(),
        "Python Executable": sys.executable,
        "Installed Modules": get_installed_packages(),
    }
    return environment_info


def get_additional_information():
    sh_script = os.path.join(os.path.dirname(__file__), "get_host_info.sh")
    p = subprocess.Popen(
        ["bash", sh_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output, _ = p.communicate()
    return output


def log_machine_details():
    system_info = {}
    try:
        system_info["System Info"] = get_system_information()
    except Exception:
        system_info["System Info"] = traceback.format_exc()

    try:
        system_info["Memory Usage"]
    except Exception:
        system_info["Memory Usage"] = traceback.format_exc()

    try:
        system_info["Disk Usage"]
    except Exception:
        system_info["Disk Usage"] = traceback.format_exc()

    try:
        system_info["Medperf Configuration"]
    except Exception:
        system_info["Medperf Configuration"] = traceback.format_exc()

    try:
        system_info["Medperf Storage Contents"]
    except Exception:
        system_info["Medperf Storage Contents"] = traceback.format_exc()

    try:
        system_info["Python Environment"]
    except Exception:
        system_info["Python Environment"] = traceback.format_exc()

    try:
        add_info = get_additional_information()
    except Exception:
        add_info = traceback.format_exc()

    debug_dict = {"Machine Details": system_info}

    logging.debug(yaml.dump(debug_dict, default_flow_style=False))
    logging.debug(add_info)


def package_logs():
    # Handle cases where the folder doesn't exist
    if not os.path.exists(config.logs_storage):
        return

    # Don't create a tarball if there's no logs to be packaged
    files = os.listdir(config.logs_storage)
    if len(files) == 0:
        return

    logfiles = []
    for file in files:
        is_logfile = re.match(r"medperf\.log(?:\.\d+)?$", file) is not None
        if is_logfile:
            logfiles.append(file)

    package_file = os.path.join(config.logs_storage, config.log_package_file)

    with tarfile.open(package_file, "w:gz") as tar:
        for file in logfiles:
            filepath = os.path.join(config.logs_storage, file)
            tar.add(filepath, arcname=os.path.basename(filepath))
